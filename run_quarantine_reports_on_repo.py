#!/usr/bin/env python

import os
import fnmatch
import re
import csv
import argparse
import behave.parser
import datetime

from contextlib import closing

from shared.utilities import display_name


QUARANTINED_INDICATOR = 'quarantined'
INACTIVE_INDICATORS = {'nyi', 'not-tested', 'needs-work'}
QUARANTINED_STATISTICS_FILE = 'reports/{repo_name}_quarantined_statistics_{time_stamp}.csv'
QUARANTINED_TESTS_FILE = 'reports/{repo_name}_quarantined_tests_{time_stamp}.csv'

QUARANTINED_STATS_COLS = ['Interface Type', 'Product Name', 'Classification 1', 'Total Tests',
                          'Active Tests', 'Quarantined Tests', 'Quarantined Percentage',
                          'Active Percentage']
QUARANTINED_TESTS_COLS = ['JIRA', 'Interface Type', 'Product Name', 'Classification 1',
                          'Feature Name', 'Scenario Name']


####################################################################################################
# Object Definitions
####################################################################################################


class Tags(object):

    def __init__(self, tag_list):
        self.tags = tag_list
        # is_quarantined will be set when checking the quarantined_jiras
        self.is_quarantined = False
        self.quarantined_jiras = self._quarantined_jiras()

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

    @property
    def is_active(self):
        return not set(self.tags) & INACTIVE_INDICATORS


class TestGrouping(object):
    def __init__(self, name):
        self.name = name
        self.quarantined_scenarios = []
        self.total_test_count = 0
        self.quarantined_test_count = 0
        self.active_test_count = 0

    def add_feature_data(self, feature):
        ''' Adds a behave features useful data to the TestGrouping.'''
        self.total_test_count += len(feature.all_scenarios)
        quarantined_scenarios = [s for s in feature.all_scenarios if s.report_tags.is_quarantined]
        self.quarantined_test_count += len(quarantined_scenarios)
        self.quarantined_scenarios.extend(quarantined_scenarios)
        self.active_test_count += len([s for s in feature.all_scenarios if s.report_tags.is_active])


class CSVWriter(object):
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

    def close(self):
        self.file.close()


####################################################################################################
# Report Generation
####################################################################################################


def _format_file_name(file_name, repo_name):
    return file_name.format(repo_name=repo_name,
                            time_stamp='{:%Y_%m_%d_%H_%M_%S_%f}'.format(datetime.datetime.now()))


def _sum_all_of(objects, attribute):
    return sum(getattr(o, attribute) for o in objects)


def _safe_round_percent(sub_section, whole):
    return round((sub_section / whole) * 100, 2) if whole else 0.0


def _quarantine_stats_report(test_groupings, product_name, interface_type):
    '''
    Creates a quarantined statistics report for the product_name provided by using the provided
    TestGroupings.  TestGroupings must be provided as an iterable of TestGrouping objects.
    '''
    def row(grouping_name, total_count, active_count, quarantined_count):
        values = [interface_type, product_name, grouping_name, total_count, active_count,
                  quarantined_count,  _safe_round_percent(quarantined_count, active_count),
                  _safe_round_percent(active_count, total_count)]
        return {col_name: value for col_name, value in zip(QUARANTINED_STATS_COLS, values)}

    with closing(CSVWriter(_format_file_name(QUARANTINED_STATISTICS_FILE, product_name),
                           QUARANTINED_STATS_COLS)) as stats_report:

        for group in test_groupings:
            stats_report.writerow(row(group.name, group.total_test_count,
                                      group.active_test_count, group.quarantined_test_count))
        stats_report.writerow(row('Total', _sum_all_of(test_groupings, 'total_test_count'),
                                  _sum_all_of(test_groupings, 'active_test_count'),
                                  _sum_all_of(test_groupings, 'quarantined_test_count')))


def _quarantine_jira_report(test_groupings, product_name, interface_type):
    '''
    Creates a quarantined JIRA report for the product_name provided by using the provided
    TestGroupings.  TestGroupings must be provided as an iterable of TestGrouping objects.
    '''
    def row(grouping_name, feature_name, scenario_name, jira_tag):
        return {col_name: value for col_name, value in zip(QUARANTINED_TESTS_COLS, [
            jira_tag, interface_type, product_name, grouping_name, feature_name, scenario_name])}

    with closing(CSVWriter(_format_file_name(QUARANTINED_TESTS_FILE, product_name),
                           QUARANTINED_TESTS_COLS)) as jira_report:
        for group in test_groupings:
            for scenario in group.quarantined_scenarios:
                if not scenario.report_tags.quarantined_jiras:
                    warning = 'WARNING: {}, {}, {} Reported quarantined without a JIRA'
                    print(warning.format(group.name, scenario.feature.name, scenario.name))
                    jira_report.writerow(row(group.name, scenario.feature.name, scenario.name, ''))
                for jira in scenario.report_tags.quarantined_jiras:
                    # If a test has multiple JIRAs associated with the quarantine, that test will be
                    # reported once for each associated JIRA.
                    jira_report.writerow(row(group.name, scenario.feature.name, scenario.name,
                                             jira))


####################################################################################################
# TestGrouping Object Creation
####################################################################################################


def _add_custom_tags(scenario):
    # Behave scenarios do not inherit feature tags by default, but for our reporting purposes we do.
    scenario.report_tags = Tags(scenario.feature.tags + scenario.tags)
    return scenario


def _grouping_name_for(file_path):
    return display_name(*os.path.split(os.path.dirname(file_path)))


def _feature_for(file_path):
    '''
    Uses the behave parser to create a Feature object form the file_path supplied, also adding the
    grouping_name, and a list of all scenarios with a custom report_tags attributed added to them.
    '''
    feature = behave.parser.parse_file(file_path)
    feature.grouping_name = _grouping_name_for(file_path)
    feature.all_scenarios = [_add_custom_tags(s) for s in feature.walk_scenarios()]
    return feature


def _test_groupings_for_repo(product_base_dir, search_hidden=False):
    '''
    Returns an iterable of TestGrouping objects created by searching the product base dir for any
    feature files, parsing them into features, and then compiling those features into TestGroupings.
    '''

    groupings = {}
    for dir_path, dir_names, file_names in os.walk(product_base_dir):
        if not search_hidden:
            # If items are removed from dir_names, os.walk will not search them.
            dir_names[:] = [x for x in dir_names if not x.startswith('.')]
        for file_name in fnmatch.filter(file_names, '*.feature'):
            feature = _feature_for(os.path.join(dir_path, file_name))
            if feature.grouping_name not in groupings:
                groupings[feature.grouping_name] = TestGrouping(feature.grouping_name)
            groupings[feature.grouping_name].add_feature_data(feature)
    return groupings.values()


####################################################################################################
# Execution
####################################################################################################


def run_reports(product_base_dir, *report_args, **product_kwargs):
    groupings = _test_groupings_for_repo(product_base_dir, **product_kwargs)

    _quarantine_stats_report(groupings, *report_args)
    _quarantine_jira_report(groupings, *report_args)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Test Reports')
    parser.add_argument('product_base_directory',
                        help='The Absolute directory of the product to run reports against')
    parser.add_argument('product', help='The product name for the report')
    parser.add_argument('interface_type', choices=['api', 'gui'],
                        help='The interface type of the product')
    parser.add_argument('--search_hidden', action='store_true', help='Include ".hidden" folders')
    args = parser.parse_args()
    run_reports(args.product_base_directory, args.product, args.interface_type,
                search_hidden=args.search_hidden)
