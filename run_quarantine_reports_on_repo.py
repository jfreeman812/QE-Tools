#!/usr/bin/env python

import os
import re
import csv
import argparse
import behave.parser
import datetime


QUARANTINED_INDICATOR = 'quarantined'
INACTIVE_INDICATORS = {'nyi', 'not-tested', 'needs-work'}
QUARANTINED_STATISTICS_FILE = 'reports/{repo_name}_quarantined_statistics_{time_stamp}.csv'
QUARANTINED_TESTS_FILE = 'reports/{repo_name}_quarantined_tests_{time_stamp}.csv'


####################################################################################################
# Object Definitions
####################################################################################################


class Tags(object):

    def __init__(self, tag_list):
        self.tags = tag_list
        # is_quarantined will be set when checking the quarantined_jiras
        self.is_quarantined = False
        self.quarantined_jiras = self._quarantined_jiras()
        self.is_active = self._is_active()

    def _quarantined_jiras(self):
        '''
        Only tags immediately following a quarantined tag, that match the JIRA regex qualify as
        quarantined jiras.  The first tag not meeting the regex signals the end of quarantined jira
        tags.
        '''
        quarantined_jiras = []
        for tag in self.tags:
            if QUARANTINED_INDICATOR == tag:
                self.is_quarantined = True
                continue
            if self.is_quarantined:
                if not re.match('(.*[^A-Z])?([A-Z][A-Z]+-[0-9]+)', tag):
                    break
                quarantined_jiras.append(tag)
        return quarantined_jiras

    def _is_active(self):
        return not set(self.tags) & INACTIVE_INDICATORS


class Product(object):
    def __init__(self, name):
        self.name = name
        self.quarantined_scenarios = []
        self.total_test_count = 0
        self.quarantined_test_count = 0
        self.active_test_count = 0

    def add_feature_data(self, feature):
        '''
        Adds a behave features useful data to the product.
        '''
        self.total_test_count += len(feature.all_scenarios)
        quarantined_scenarios = [s for s in feature.all_scenarios if s.report_tags.is_quarantined]
        self.quarantined_test_count += len(quarantined_scenarios)
        self.quarantined_scenarios.extend(quarantined_scenarios)
        self.active_test_count += len([s for s in feature.all_scenarios if s.report_tags.is_active])


class CSVLogger(object):
    def __init__(self, path, columns):
        self.path = path
        if os.path.exists(self.path):
            os.remove(self.path)
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self.file = open(self.path, 'a')
        self.rowwriter = csv.DictWriter(self.file, fieldnames=columns)
        self.rowwriter.writeheader()

    def writerow(self, row):
        self.rowwriter.writerow(row)
        self.file.flush()

    def done(self):
        self.file.close()


####################################################################################################
# Report Generation
####################################################################################################


def _product_name(product_name):
    return product_name.replace('_', ' ').title()


def _format_file_name(file_name, repo_name):
    return file_name.format(repo_name=repo_name,
                            time_stamp='{:%Y_%m_%d_%H_%M_%S_%f}'.format(datetime.datetime.now()))


def _sum_all_of(objects, attribute):
    return sum(getattr(o, attribute) for o in objects)


def _safe_round_percent(sub_section, whole):
    return round((sub_section / whole) * 100, 2) if whole else 0.0


def _quarantine_stats_report(products, repo_name):
    '''
    Creates a quarantined statistics report for the repo_name provided by using the provided
    products.  Products must be provided as an iterable of product objects.
    '''
    def row(product_name, total_count, active_count, quarantined_count):
        return {
            'PRODUCT_NAME': _product_name(product_name),
            'TOTAL_TEST_COUNT': total_count,
            'ACTIVE_TEST_COUNT': active_count,
            'QUARANTINED_TEST_COUNT': quarantined_count,
            'QUARANTINED_PERCENTAGE': _safe_round_percent(quarantined_count, active_count),
            'ACTIVE_PERCENTAGE': _safe_round_percent(active_count, total_count)
        }

    stats_report = CSVLogger(_format_file_name(QUARANTINED_STATISTICS_FILE, repo_name), [
        'PRODUCT_NAME', 'TOTAL_TEST_COUNT', 'ACTIVE_TEST_COUNT',
        'QUARANTINED_TEST_COUNT', 'QUARANTINED_PERCENTAGE', 'ACTIVE_PERCENTAGE'])

    for product in products:
        stats_report.writerow(row(product.name, product.total_test_count, product.active_test_count,
                                  product.quarantined_test_count))
    stats_report.writerow(row('All Products', _sum_all_of(products, 'total_test_count'),
                              _sum_all_of(products, 'active_test_count'),
                              _sum_all_of(products, 'quarantined_test_count')))
    stats_report.done()


def _quarantine_jira_report(products, repo_name):
    '''
    Creates a quarantined JIRA report for the repo_name provided by using the provided products.
    Products must be provided as an iterable of product objects.
    '''
    jira_report = CSVLogger(_format_file_name(QUARANTINED_TESTS_FILE, repo_name), [
        'JIRA', 'PRODUCT_NAME', 'FEATURE_NAME', 'SCENARIO_NAME'])

    def row(product_name, feature_name, scenario_name, jira):
        return {
            'PRODUCT_NAME': _product_name(product_name),
            'FEATURE_NAME': feature_name,
            'SCENARIO_NAME': scenario_name,
            'JIRA': jira
        }

    for product in products:
        for scenario in product.quarantined_scenarios:
            if not scenario.report_tags.quarantined_jiras:
                # Scenarios may be quarantined without JIRAs, though this is rare and undesirable.
                jira_report.writerow(row(product.name, scenario.feature.name, scenario.name, ''))
            for jira in scenario.report_tags.quarantined_jiras:
                # If a test has multiple JIRAs associated with the quarantine, that test will be
                # reported once for each associated JIRA.
                jira_report.writerow(row(product.name, scenario.feature.name, scenario.name, jira))
    jira_report.done()


####################################################################################################
# Product Object Creation
####################################################################################################


def _add_custom_tags(scenario, feature_tags):
    # Behave scenarios do not inherit feature tags by default, but for our reporting purposes we
    # we do.
    scenario.report_tags = Tags(feature_tags + scenario.tags)
    return scenario


def _feature_for(file_path):
    '''
    Uses the behave parser to create a Feature object form the file_path supplied, also adding the
    product, and a list of all scenarios with a custom report_tags attributed added to them.
    '''
    feature = behave.parser.parse_file(file_path)
    feature.product = os.path.basename(os.path.split(file_path)[0])
    feature.all_scenarios = [_add_custom_tags(s, feature.tags) for s in feature.walk_scenarios()]
    return feature


def _is_feature_file(name):
    return name.lower().endswith('.feature')


def _products_for_repo(repo_base_dir):
    '''
    Returns an iterable of Product objects created by searching the repo_base_dir for any feature
    files, parsing them into features, and then compiling those features into products.
    '''

    products = {}
    for dir_path, dir_names, file_names in os.walk(repo_base_dir):
        if '.git' in dir_names:
            dir_names.remove('.git')
        for file_name in filter(_is_feature_file, file_names):
            feature = _feature_for(os.path.join(dir_path, file_name))
            if feature.product not in products:
                products[feature.product] = Product(feature.product)
            products[feature.product].add_feature_data(feature)
    return products.values()


####################################################################################################
# Execution
####################################################################################################

def run_reports(repo_base_dir):
    products = _products_for_repo(repo_base_dir)
    repo_name = os.path.basename(os.path.normpath(repo_base_dir))

    _quarantine_stats_report(products, repo_name)
    _quarantine_jira_report(products, repo_name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Test Reports')
    parser.add_argument('repo_base_directory',
                        help='The Absolute directory of the repo to run reports against')
    args = parser.parse_args()
    run_reports(args.repo_base_directory)
