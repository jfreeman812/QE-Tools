#!/usr/bin/env python

import os
import fnmatch
import re
import csv
import argparse
import behave.parser
import datetime
import json

from collections import defaultdict
from contextlib import closing
from test_tags import TestTags

from shared.utilities import display_name, padded_list


QUARANTINED_INDICATOR = 'quarantined'
TAG_DEFINITION_FILE = 'tags.md'
REPORT_PATH = 'reports'
QUARANTINED_STATISTICS_FILE = '{repo_name}_quarantined_statistics_{time_stamp}.{ext}'
COVERAGE_REPORT_FILE = '{repo_name}_coverage_report_{time_stamp}.{ext}'
JIRA_RE = re.compile('(.*[^A-Z])?([A-Z][A-Z]+-[0-9]+)')

####################################################################################################
# Globals
####################################################################################################


class ErrorAggregator(object):

    def __init__(self):
        self.error_list = []

    def __call__(self, format_str, *format_args):
        self.error_list.append(format_str.format(*format_args))

    @property
    def errors(self):
        if not self.error_list:
            return ''
        return 'REPORTING ERRORS: \n{}'.format('\n'.join(self.error_list))


# Any display name in nuisance_category_names will be omitted from the categories.  'features' is
# ignored as it is a special name required in cucumber and meaningless for reporting.
nuisance_category_names = ['features']
tag_definitions = TestTags('tags.md', strip_at=True)
reporting_errors = ErrorAggregator()


####################################################################################################
# Object Definitions
####################################################################################################


class Tags(object):

    def __init__(self, tag_list, scenario_name):
        self.tags = tag_list
        self.is_quarantined = QUARANTINED_INDICATOR in self.tags
        self.scenario_name = scenario_name
        self.jiras = self._jiras()

    def _jiras(self):
        '''
        Returns a dictionary of {status_key: [associated jira tags]}.  If the jira is not associated
        with a status, the status key will be 'jiras'.  If a status does not have any jiras
        associated with it, an error will be logged.
        '''
        jira_collection = defaultdict(list)
        status = None
        for tag in self.tags:
            if tag in tag_definitions.groups['status']:
                status = tag
                # A status existing with an empty list indicates that no jiras were associated with
                # that status.
                jira_collection[status]
                continue
            if JIRA_RE.match(tag):
                jira_collection[status or 'JIRAs'].append(tag)
                continue
            status = None

        for status, jiras in jira_collection:
            if not jiras:
                reporting_errors('ERROR: JIRA not found for Scenario: {}, Status: {}, Tags {}',
                                 self.scenario_name, status, self.tags)
        return jira_collection

    def property_from_tags(self, property_name):

        def single_matching_tag(expected_tags, default=None):
            base_error_msg = 'ERROR: Property "{}", Scenario: {}, has'.format(property_name,
                                                                              self.scenario_name)
            intersection = set(self.tags) & set(expected_tags)
            if len(intersection) > 1:
                reporting_errors('{} multiple mutually exclusive Tags: {}', base_error_msg,
                                 intersection)
            if not intersection and not default:
                reporting_errors('{} No Matching Tag or Default for Tags: {}, Available Tags: {}',
                                 base_error_msg, self.tags, expected_tags)
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


####################################################################################################
# Report Generation
####################################################################################################


def _csv_cols_from(base_csv_col_name, padded_values):
    '''
    Takes the base csv column name and padded values list and returns a list of CSV column names to
    values: [('Column 1', value1 or ''), ('Column 2', value2 or ''), ..].  The padded values should
    be supplied as the same length every time.
    '''
    return [(base_csv_col_name.format(c), v) for c, v in enumerate(padded_values, start=1)]


def _empty_str_padded_list(list_or_none, pad_to_length):
    '''
    Returns a padded list of a length defined by pad_to_length, the padding will be an empty string.
    '''
    list_to_pad = list_or_none or []
    return padded_list(list_to_pad, pad_to_length, '')


def _sum_all_of(objects, attribute):
    return sum(getattr(o, attribute) for o in objects)


def _safe_round_percent(sub_section, whole):
    return round((sub_section / whole) * 100, 2) if whole else 0.0


class ReportWriter(object):
    base_file_name = ''
    _max_category_len = None

    def __init__(self, test_groupings, product_name, interface_type, project, output_dir):
        self.test_groups = test_groupings
        self.product_name = product_name
        self.interface_type = interface_type
        self.project = project
        self.output_dir = output_dir
        self.data = self._data()
        self._write_json_report()
        self._write_csv_report()

    @property
    def _max_categories(self):
        '''Returns the length of the largest category list in the test groups'''
        if self._max_category_len is None:
            self._max_category_len = max(len(g.categories) for g in self.test_groups)
        return self._max_category_len

    def csv_mappings(self):
        '''
        Returns a common list of tuples mapping json data keys to csv column names in the desired
        order of the csv columns for the csv reports.
        '''
        return [
            ('product', 'Product'),
            ('project', 'Project'),
            ('interface', 'Interface Type'),
            ('categories', lambda v: _csv_cols_from(
                'Category {}', _empty_str_padded_list(v, self._max_categories))),
        ]

    def _data_item(self, categories, **additional_data):
        '''
        Takes the categories and any additional data and returns a data dictionary with common
        reporting values
        '''
        return {
            'product': self.product_name,
            'project': self.project,
            'interface': self.interface_type,
            'categories': categories,
            **additional_data
        }

    def _data(self):
        '''
        This method should be overridden to return a list of dictionaries containing reporting data
        '''
        raise NotImplementedError('_data method must be overridden')

    def _format_file_name(self, extension):
        '''
        Formats the base_file_name attribute that should be overridden with a string having the
        following format keywords in this example: "{repo_name}_some_report_{time_stamp}.{ext}"
        '''
        format_kwargs = {
            'repo_name': self.product_name,
            'time_stamp': '{:%Y_%m_%d_%H_%M_%S_%f}'.format(datetime.datetime.now()),
            'ext': extension,
        }
        return self.base_file_name.format(**format_kwargs)

    def _format_and_return_file_path(self, *file_name_args):
        '''
        Returns the full formatted file path, and ensures that the directory exists and there is
        not a file with the current name existing there.
        '''
        file_path = os.path.join(self.output_dir, self._format_file_name(*file_name_args))
        if os.path.exists(file_path):
            os.remove(file_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        return file_path

    def _write_json_report(self):
        '''
        Writes a .json file with the contents of self.data to the base_file_name .json extension
        '''
        with open(self._format_and_return_file_path('json'), 'w') as f:
            json.dump(self.data, f, indent=4)

    def _write_csv_report(self):
        '''
        Writes a .csv file, mapping the contents of self.data to csv columns by calling
        self._csv_data_from_json
        '''
        column_names = [col_name for col_name, _ in self._csv_data_from_json({})]
        with closing(CSVWriter(self._format_and_return_file_path('csv'), column_names)) as csv_file:
            csv_file.writerows([dict(self._csv_data_from_json(d)) for d in self.data])

    def _csv_data_from_json(self, json_data):
        '''
        Returns a list of tuples of (CSV_COL_NAME, VALUE) in the same order as supplied in
        self.csv_mappings If the 2nd item in the mapping tuple (csv_name), is a function, it will be
        called passing in the value, and an iterable will be expected as a return.
        json_data:  Dictionary of json_names to values.
        '''
        csv_data = []
        for json_name, csv_name in self.csv_mappings():
            value = json_data.get(json_name)
            csv_data.extend(csv_name(value) if callable(csv_name) else [(csv_name, value)])
        return csv_data


class QuarantinedStatsReport(ReportWriter):
    base_file_name = QUARANTINED_STATISTICS_FILE

    def csv_mappings(self):
        '''
        Returns a list of tuples mapping json data keys to csv column names in the desired order of
        the csv columns for the csv statistics report.  Includes the common csv mappings and those
        defined here.
        '''
        return [
            *super().csv_mappings(),
            ('total_tests', 'Total Tests'),
            ('active_tests', 'Active Tests'),
            ('quarantined_tests', 'Quarantined Tests'),
            ('quarantined_percentage', 'Quarantined Percentage'),
            ('active_percentage', 'Active Percentage'),
        ]

    def _stats_data(self, categories, total_count, active_count, quarantined_count):
        '''
        Returns a dictionary of data relevant to one grouping for the quarantined statistics report
        '''
        stats_data = {
            'total_tests': total_count,
            'active_tests': active_count,
            'quarantined_tests': quarantined_count,
            'quarantined_percentage': _safe_round_percent(quarantined_count, active_count),
            'active_percentage': _safe_round_percent(active_count, total_count),
        }
        return self._data_item(categories, **stats_data)

    def _data(self):
        '''Returns a list of dictionaries containing data for the quarantined statistics report'''
        data = [self._stats_data(g.categories, g.total_test_count, g.active_test_count,
                                 g.quarantined_test_count) for g in self.test_groups]
        data.append(self._stats_data(['Total'], _sum_all_of(self.test_groups, 'total_test_count'),
                                     _sum_all_of(self.test_groups, 'active_test_count'),
                                     _sum_all_of(self.test_groups, 'quarantined_test_count')))
        return data


class CoverageReport(ReportWriter):
    base_file_name = COVERAGE_REPORT_FILE
    _max_jiras_len = None

    @property
    def _max_jiras(self):
        '''Returns the length of the largest jira list in the test groups'''
        if self._max_jiras_len is None:
            self._max_jiras_len = max(len(s.report_tags.quarantined_jiras)
                                      for g in self.test_groups for s in g.all_scenarios)
        return self._max_jiras_len

    def csv_mappings(self):
        '''
        Returns a list of tuples mapping json data keys to csv column names in the desired order of
        the csv columns for the csv coverage report.  Includes the common csv mappings and those
        defined here.
        '''
        return [
            *super().csv_mappings(),
            ('feature_name', 'Feature Name'),
            ('test_name', 'Test Name'),
            ('polarity', 'Polarity'),
            ('priority', 'Priority'),
            ('suite', 'Suite'),
            ('status', 'Status'),
            ('execution', 'Execution Method'),
            ('JIRAs', lambda v: _csv_cols_from(
                'JIRA {}', _empty_str_padded_list(v, self._max_jiras))),
        ]

    def _scenario_data(self, categories, scenario):
        '''Returns a dictionary of data relevant to one scenario for the coverage report'''
        scenario_data = {
            'test_name': scenario.name,
            'feature_name': scenario.feature.name,
            'JIRAs': scenario.report_tags.quarantined_jiras,
            **{name: scenario.report_tags.property_from_tags(name)
               for name in ['polarity', 'priority', 'suite', 'status', 'execution']}
        }
        return self._data_item(categories, **scenario_data)

    def _data(self):
        '''Returns a list of dictionaries containing data for the coverage report'''
        return [self._scenario_data(g.categories, s)
                for g in self.test_groups for s in g.all_scenarios]


class CSVWriter(object):
    def __init__(self, path, columns):
        self.file = open(path, 'a')
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
# TestGrouping Object Creation
####################################################################################################


def _add_custom_tags(scenario):
    # Behave scenarios do not inherit feature tags by default, but for our reporting purposes we do.
    scenario.report_tags = Tags(scenario.feature.tags + scenario.tags, scenario.name)
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
        name = display_name(product_path, category)
        if name.lower() not in nuisance_category_names:
            categories.append(name)
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
    QuarantinedStatsReport(groupings, product_name, *report_args)
    CoverageReport(groupings, product_name, *report_args)
    assert not reporting_errors.errors, reporting_errors.errors


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Test Reports')
    parser.add_argument('repo_base_directory',
                        help='The Absolute directory of the repo to run reports against')
    parser.add_argument('interface_type', choices=['api', 'gui'],
                        help='The interface type of the product')
    product_help = 'The additional product directory, if not supplied the repo is assumed to be' \
                   ' the product.'
    parser.add_argument('-p', '--product_dir', nargs='?', default='', help=product_help)
    project_help = 'The name of the project, if one is not supplied n/a will be used.'
    parser.add_argument('-j', '--project', nargs='?', default='n/a', help=project_help)
    parser.add_argument('-o', '--output-dir', default=REPORT_PATH,
                        help='Output directory for the generated report files.')
    parser.add_argument('--search_hidden', action='store_true', help='Include ".hidden" folders')
    args = parser.parse_args()
    run_reports(args.repo_base_directory, args.product_dir, args.interface_type, args.project,
                args.output_dir, search_hidden=args.search_hidden)
