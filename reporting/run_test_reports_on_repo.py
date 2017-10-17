#!/usr/bin/env python

import os
import fnmatch
import re
import csv
import argparse
import behave.parser
import datetime
import json

from contextlib import closing
from test_tags import TestTags

from shared.utilities import display_name, padded_list


QUARANTINED_INDICATOR = 'quarantined'

TAG_DEFINITION_FILE = 'tags.md'
QUARANTINED_STATISTICS_FILE = 'reports/{repo_name}_quarantined_statistics_{time_stamp}.csv'
QUARANTINED_TESTS_FILE = 'reports/{repo_name}_quarantined_tests_{time_stamp}.csv'
COVERAGE_REPORT_CSV = 'reports/{repo_name}_coverage_report_{time_stamp}.csv'
COVERAGE_REPORT_JSON = 'reports/{repo_name}_coverage_report_{time_stamp}.json'

QUARANTINED_STATS_COLS = ['Interface Type', 'Product Name', 'Project', 'Category 1', 'Category 2',
                          'Category 3', 'Total Tests', 'Active Tests', 'Quarantined Tests',
                          'Quarantined Percentage', 'Active Percentage']
QUARANTINED_TESTS_COLS = ['JIRA', 'Interface Type', 'Product Name', 'Project', 'Category 1',
                          'Category 2', 'Category 3', 'Feature Name', 'Scenario Name']
MAX_CATEGORIES = 3
tag_definitions = TestTags('tags.md', strip_at=True)

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

    def property_from_tags(self, property_name):

        def single_matching_tag(expected_tags, default=None):
            intersection = set(self.tags) & set(expected_tags)
            if len(intersection) > 1:
                error_msg = 'Warning: Property "{}" has multiple, mutually exclusive tags: {}'
                print(error_msg.format(property_name, intersection))
            return intersection.pop() if intersection else default

        valid_property_tags = tag_definitions.groups[property_name]
        default_tag = tag_definitions.group_default.get(property_name)
        tag_name = single_matching_tag(valid_property_tags, default=default_tag)
        return tag_definitions.report_names.get(tag_name, default_tag)

    @property
    def is_active(self):
        return not set(self.tags) & (tag_definitions.groups['status'] - {QUARANTINED_INDICATOR})


class TestGrouping(object):
    def __init__(self, name, categories):
        self.name = name
        self.categories = categories
        self.all_scenarios = []
        self.quarantined_scenarios = []
        self.total_test_count = 0
        self.quarantined_test_count = 0
        self.active_test_count = 0

    def add_feature_data(self, feature):
        ''' Adds a behave features useful data to the TestGrouping.'''
        self.all_scenarios.extend(feature.all_scenarios)
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

    def writerows(self, rows):
        self.rowwriter.writerows(rows)

    def close(self):
        self.file.close()


####################################################################################################
# Report Generation
####################################################################################################


def _padded_categories(categories):
    categories = categories or []
    return padded_list(categories, MAX_CATEGORIES, '')


def _csv_categories(cat_csv_name, cat_list):
    '''
    Takes the category base name as the cat_csv_name and category list value from the json (or none)
    and returns a list of category CSV column names to category values, that is always the length of
    MAX_CATEGORIES. [('Category 1', value1 or ''), ('Category 2', value2 or ''), ..]
    '''
    categories = _padded_categories(cat_list)
    return [(cat_csv_name.format(count), value) for count, value in enumerate(categories, start=1)]


def _csv_data_from_json(json_data, mappings):
    '''
    Takes the supplied json_data and mappings and returns a list of tuples of (CSV_COL_NAME, VALUE)
    in the same order specified in the mappings.  If the 2nd item in the mapping tuple (csv_name),
    is a function, it will be called passing in the value, and an iterable will be expected as a
    return.
    json_data:  Dictionary of json_names to values.
    mappings:  List of tuples [(json_key_name, csv_column_name), ...] representing the desired order
    of the csv data.
    '''
    csv_data = []
    for json_name, csv_name in mappings:
        value = json_data.get(json_name)
        csv_data.extend(csv_name(value) if callable(csv_name) else [(csv_name, value)])
    return csv_data


def _write_json_to_file(file_name, json_object):
    with open(file_name, 'w') as f:
        json.dump(json_object, f, indent=4)


def _write_csv_to_file(file_name, json_data_list, mappings):
    '''
    Writes the json_data_list to a csv file using the mappings supplied to provide the column names
    and the order of the data.
    '''
    column_names = [col_name for col_name, _ in _csv_data_from_json({}, mappings)]
    with closing(CSVWriter(file_name, column_names)) as csv_file:
        csv_file.writerows([dict(_csv_data_from_json(d, mappings)) for d in json_data_list])


def _format_file_name(file_name, repo_name):
    return file_name.format(repo_name=repo_name,
                            time_stamp='{:%Y_%m_%d_%H_%M_%S_%f}'.format(datetime.datetime.now()))


def _sum_all_of(objects, attribute):
    return sum(getattr(o, attribute) for o in objects)


def _safe_round_percent(sub_section, whole):
    return round((sub_section / whole) * 100, 2) if whole else 0.0


def _quarantine_stats_report(test_groupings, product_name, interface_type, project, *report_args):
    '''
    Creates a quarantined statistics report for the product_name provided by using the provided
    TestGroupings.  TestGroupings must be provided as an iterable of TestGrouping objects.
    '''
    def row(categories, total_count, active_count, quarantined_count):
        values = [interface_type, product_name, project, *categories, total_count, active_count,
                  quarantined_count, _safe_round_percent(quarantined_count, active_count),
                  _safe_round_percent(active_count, total_count)]
        return {col_name: value for col_name, value in zip(QUARANTINED_STATS_COLS, values)}

    with closing(CSVWriter(_format_file_name(QUARANTINED_STATISTICS_FILE, product_name),
                           QUARANTINED_STATS_COLS)) as stats_report:

        for group in test_groupings:
            stats_report.writerow(row(_padded_categories(group.categories),
                                      group.total_test_count, group.active_test_count,
                                      group.quarantined_test_count))
        stats_report.writerow(row(_padded_categories(['Total']),
                                  _sum_all_of(test_groupings, 'total_test_count'),
                                  _sum_all_of(test_groupings, 'active_test_count'),
                                  _sum_all_of(test_groupings, 'quarantined_test_count')))


def _quarantine_jira_report(test_groupings, product_name, interface_type, project, *report_args):
    '''
    Creates a quarantined JIRA report for the product_name provided by using the provided
    TestGroupings.  TestGroupings must be provided as an iterable of TestGrouping objects.
    '''
    def row(categories, feature_name, scenario_name, jira_tag):
        return {col_name: value for col_name, value in zip(QUARANTINED_TESTS_COLS, [
            jira_tag, interface_type, product_name, project, *categories, feature_name,
            scenario_name])}

    with closing(CSVWriter(_format_file_name(QUARANTINED_TESTS_FILE, product_name),
                           QUARANTINED_TESTS_COLS)) as jira_report:
        for group in test_groupings:
            for scenario in group.quarantined_scenarios:
                if not scenario.report_tags.quarantined_jiras:
                    warning = 'WARNING: {}, {}, {} Reported quarantined without a JIRA'
                    print(warning.format(group.name, scenario.feature.name, scenario.name))
                    jira_report.writerow(row(_padded_categories(group.categories),
                                             scenario.feature.name, scenario.name, ''))
                for jira in scenario.report_tags.quarantined_jiras:
                    # If a test has multiple JIRAs associated with the quarantine, that test will be
                    # reported once for each associated JIRA.
                    jira_report.writerow(row(_padded_categories(group.categories),
                                             scenario.feature.name, scenario.name, jira))


def _coverage_data(test_groupings, product_name, interface_type, project):
    def _data():
        return {
            'product': product_name,
            'project': project,
            'interface': interface_type,
        }

    output = []
    for group in test_groupings:
        for scenario in group.all_scenarios:
            coverage_data = _data()
            coverage_data['test_name'] = scenario.name
            coverage_data['categories'] = group.categories
            # The below names share the same json key name and group name from tags.md
            for name in ['polarity', 'priority', 'suite', 'status', 'execution']:
                coverage_data[name] = scenario.report_tags.property_from_tags(name)
            output.append(coverage_data)
    return output


def _coverage_report(test_groupings, product_name, interface_type, project, write_to_json):
    output = _coverage_data(test_groupings, product_name, interface_type, project)

    if write_to_json:
        _write_json_to_file(_format_file_name(COVERAGE_REPORT_JSON, product_name), output)
        return

    # These mappings are tuples representing json data keys and csv column names (or a function) in
    # the desired order for the coverage report csv.  [(json_key, csv_col_name), ....]
    csv_mappings = [
        ('product', 'Product'), ('project', 'Project'), ('interface', 'Interface Type'),
        ('categories', lambda v: _csv_categories('Category {}', v)), ('test_name', 'Test Name'),
        ('polarity', 'Polarity'), ('priority', 'Priority'), ('suite', 'Suite'),
        ('status', 'Status'), ('execution', 'Execution Method')]

    _write_csv_to_file(_format_file_name(COVERAGE_REPORT_CSV, product_name), output, csv_mappings)


####################################################################################################
# TestGrouping Object Creation
####################################################################################################


def _add_custom_tags(scenario):
    # Behave scenarios do not inherit feature tags by default, but for our reporting purposes we do.
    scenario.report_tags = Tags(scenario.feature.tags + scenario.tags)
    return scenario


def _categories(grouping_name, product_path):
    '''
    Returns a list of categories for the grouping_name supplied. Categories are created by splitting
    the grouping name apart and turning each piece into a display name.  The highest level of the
    directory is returned as the first item, and the lowest level as the last.
    Ex:  grouping_name = 'parent_dir/sub_dir/lowest_dir' -> ['parent_dir', 'sub_dir', 'lowest_dir']
    '''
    categories = []
    for category in os.path.normpath(grouping_name).split(os.sep):
        categories.append(display_name(product_path, category))
        product_path = os.path.join(product_path, category)
    return categories


def _feature_for(file_path, product_path):
    '''
    Uses the behave parser to create a Feature object form the file_path supplied, also adding the
    grouping_name, and a list of all scenarios with a custom report_tags attributed added to them.
    '''
    feature = behave.parser.parse_file(file_path)
    feature.grouping_name = os.path.relpath(os.path.dirname(file_path), product_path)
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
            feature = _feature_for(os.path.join(dir_path, file_name), product_base_dir)
            if feature.grouping_name not in groupings:
                categories = _categories(feature.grouping_name, product_base_dir)
                groupings[feature.grouping_name] = TestGrouping(feature.grouping_name, categories)
            groupings[feature.grouping_name].add_feature_data(feature)
    return groupings.values()


####################################################################################################
# Execution
####################################################################################################


def run_reports(repo_base_directory, product_dir, *report_args, **product_kwargs):
    product_base_dir = os.path.join(repo_base_directory, product_dir)
    groupings = _test_groupings_for_repo(product_base_dir, **product_kwargs)

    product_name = display_name(*os.path.split(os.path.normpath(product_base_dir)))
    _quarantine_stats_report(groupings, product_name, *report_args)
    _quarantine_jira_report(groupings, product_name, *report_args)
    _coverage_report(groupings, product_name, *report_args)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Test Reports')
    parser.add_argument('repo_base_directory',
                        help='The Absolute directory of the repo to run reports against')
    parser.add_argument('interface_type', choices=['api', 'gui'],
                        help='The interface type of the product')
    product_help = 'The additional product directory, if not supplied the repo is assumed to be' \
                   ' the product.'
    parser.add_argument('-p', '--product', nargs='?', default='', help=product_help)
    project_help = 'The name of the project, if one is not supplied n/a will be used.'
    parser.add_argument('-j', '--project', nargs='?', default='n/a', help=project_help)
    parser.add_argument('--search_hidden', action='store_true', help='Include ".hidden" folders')
    json_help = 'Output json file instead of csv (currently only supported for coverage report)'
    parser.add_argument('--json', action='store_true', help=json_help)
    args = parser.parse_args()
    run_reports(args.repo_base_directory, args.product, args.interface_type, args.project,
                args.json, search_hidden=args.search_hidden)
