#!/usr/bin/env python
from collections import defaultdict, namedtuple
from contextlib import closing
import csv
import datetime
from itertools import chain
import json
import os
import re
import socket
import time  # Needed because Python 2.7 doesn't support datetime.datetime.now().timestamp()
try:
    from urllib import parse
except ImportError:
    import urlparse as parse

import attr
import requests
from tableread import SimpleRSTReader

from qecommon_tools import padded_list


NO_STATUS_JIRA_KEY = 'JIRAs'
TAG_DEFINITION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'coverage.rst')
REPORT_PATH = 'reports'
COVERAGE_REPORT_FILE = '{repo_name}_coverage_report_{time_stamp}.{ext}'
JIRA_RE = re.compile('(.*[^A-Z])?([A-Z][A-Z]+-[0-9]+)')
SPLUNK_COLLECTOR_HOSTNAME = 'httpc.secops.rackspace.com'
SPLUNK_COLLECTOR_URL = 'https://{}:8088/services/collector'.format(SPLUNK_COLLECTOR_HOSTNAME)
SPLUNK_REPORT_INDEX = 'rax_temp_60'
SPLUNK_COVERAGE_INDEX = 'rax_qe_coverage'

####################################################################################################
# Globals
####################################################################################################
coverage_tables = SimpleRSTReader(TAG_DEFINITION_FILE)
status_table = coverage_tables['Status'].exclude_by(tag='')
JIRA_STATUS_DISPLAY_NAMES = [NO_STATUS_JIRA_KEY] + sorted(status_table.get_fields('report_as'))


@attr.s
class TestCoverage(object):
    name = attr.ib()
    categories = attr.ib(default=attr.Factory(list))
    tags = attr.ib(default=attr.Factory(list))
    feature_name = attr.ib(default='')
    parent_tags = attr.ib(default=attr.Factory(list))
    # Pre-defined Constants
    jiras = attr.ib(default=attr.Factory(lambda: defaultdict(list)), init=False)
    attributes = attr.ib(default=attr.Factory(dict), init=False)
    errors = attr.ib(default=attr.Factory(list), init=False)

    def build(self):
        '''Build the necessary objects from the provided tag list(s).'''
        self.organize_prescriptives()
        self.organize_structureds()
        self.organize_jiras()

    def organize_prescriptives(self):
        '''Convert prescriptive tags into their appropriate attributes.'''
        # The first coverage tables lists all the attributes, so to find the prescriptive tables,
        # we can skip this table and use the remaining ones.
        for attribute in coverage_tables.tables[1:]:
            self.attributes[attribute] = self._build_prescriptive(attribute)

    def _build_prescriptive(self, attribute):
        '''Given a single attribute, find all appropriate tags and validate.'''
        attribute_table = coverage_tables[attribute]
        # Get all valid attribute tags, excluding the default
        valid_tags = attribute_table.exclude_by(tag='').get_fields('tag')
        # Get the default attribute tag, if provided
        default_value = attribute_table.matches_all(tag='').get_fields('report_as')
        default_value = default_value[0] if default_value else ''
        # Find the intersection between the valid tags and all provided tags
        found_tags = set(self.tags + self.parent_tags) & set(valid_tags)
        # Validate the tags
        if len(found_tags) > 1:
            message = '{}:Multiple tags for prescriptive attribute {}: {}'
            self.errors.append(message.format(self.name, attribute, found_tags))
        if not found_tags and not default_value:
            message = '{}:No tag for prescriptive attribute {}. Must be one of {}'
            self.errors.append(message.format(self.name, attribute, valid_tags))
        if found_tags:
            return attribute_table.matches_all(tag=found_tags.pop()).data[0].report_as
        # To signal a table default should be pulled from the command line interface, the default
        # value is stored as ``<argument_value>``. This regex converts this format into an empty
        # string for easier parsing.
        return re.sub('`.*`', '', default_value)

    def organize_structureds(self):
        '''Convert structured tags into their appropriate attributes.'''
        tag_categories = self.structured_tag('category', multiple=True)
        if len(tag_categories) > 1:
            self.errors.append('{}:There can only be one category tag per test'.format(self.name))
        self.attributes['Categories'] = tag_categories[0] if tag_categories else self.categories
        self.attributes['Projects'] = self.structured_tag('project')

    def organize_jiras(self):
        for tag_list in (self.tags, self.parent_tags):
            self._organize_jiras(tag_list)
        for status in (x for x in self.jiras if not self.jiras[x]):
            self.errors.append('{}:JIRA not found for status: {}'.format(self.name, status))

    def _organize_jiras(self, tag_list):
        '''
        Iterate over all provided tags and update the jiras variables. If the JIRA is associated
        with a status tag, that status will be the key; otherwise the key will be 'JIRAs'.
        '''
        status = None
        for tag in tag_list:
            if tag in status_table.get_fields('tag'):
                status = status_table.matches_all(tag=tag).data[0].report_as
                # Since a status with an empty list indicates that no JIRAs were associated with
                # that status, we need to explicity create the status key with the default value
                # for validation later.
                self.jiras[status]
                continue
            if JIRA_RE.match(tag):
                self.jiras[status or NO_STATUS_JIRA_KEY].append(tag)
                continue
            status = None

    def structured_tag(self, tag_key, multiple=False):
        '''Given a tag key, find the appropriate tag and return the attribute value.'''
        tag_list = chain(self.tags, self.parent_tags)
        matches = [x for x in tag_list if x.startswith('{}:'.format(tag_key))]
        if multiple:
            return [x.split(':')[1:] for x in matches]
        return [x.split(':', 1)[1] for x in matches]


@attr.s
class TestGroup(object):
    # Pre-defined Constants
    tests = attr.ib(default=attr.Factory(list), init=False)
    errors = attr.ib(default=attr.Factory(list), init=False)

    def add(self, name, categories=None, tags=None, feature_name='', parent_tags=None):
        test = TestCoverage(name=name, categories=categories, tags=tags, feature_name=feature_name,
                            parent_tags=parent_tags or [])
        test.build()
        self.tests.append(test)
        self.errors.extend(test.errors)

    def validate(self):
        assert not self.errors, '\n'.join(self.errors)


####################################################################################################
# Report Generation
####################################################################################################


def _empty_str_padded_list(list_or_none, pad_to_length):
    '''
    Returns a padded list of a length defined by pad_to_length, the padding will be an empty string.
    '''
    list_to_pad = list_or_none or []
    return padded_list(list_to_pad, pad_to_length, '')


def _hostname_from_env():
    jenkins_url = os.environ.get('JENKINS_URL')
    return parse.urlparse(jenkins_url).netloc if jenkins_url else None


class ReportWriter(object):
    base_file_name = ''
    _source = None

    def __init__(self, test_group, business_unit, team, product_name, interface_type, output_dir,
                 splunk_token=None):
        self.test_group = test_group
        self.business_unit = business_unit
        self.team = team
        self.product_name = product_name
        self.interface_type = interface_type
        self.output_dir = output_dir
        self._splunk_token = splunk_token
        self._max_lens = {}
        self.data = self._data()
        self._json_keys_that_exist = {k for d in self.data for k in d.keys()}
        self._write_json_report()
        self._write_csv_report()
        if self._splunk_token:
            self._send_to_splunk()

    def _max_len(self, key):
        '''
        Caches and returns the max length of any value for that key if the value is a list, if the
        value is not not a list, does not exist, or exists with no length, will return 0
        '''
        if key not in self._max_lens:
            self._max_lens[key] = max(len(d.get(key) if isinstance(d.get(key), list) else [])
                                      for d in self.data)
        return self._max_lens[key]

    def _csv_heading_order(self):
        '''The csv heading order that the data will appear in on the reports'''
        return [
            'Business Unit',
            'Product',
            'Project',
            'Interface Type',
            'Categories',
        ]

    def _csv_cols_from(self, heading, list_or_none):
        '''
        Returns a list tuples of CSV column names and values corresponding to the max length of any
        list value found for the heading provided.  If the heading does not exist, has only empty
        lists as values,or does not have lists as values will return an empty list
        '''
        padded_values = _empty_str_padded_list(list_or_none, self._max_len(heading))
        return [('{} {}'.format(heading, i), v) for i, v in enumerate(padded_values, start=1)]

    def _data_item(self, **additional_data):
        '''
        Takes the categories and any additional data and returns a data dictionary with common
        reporting values
        '''
        data_item = {'Business Unit': self.business_unit, 'Team': self.team,
                     'Product': self.product_name, 'Interface Type': self.interface_type}
        data_item.update(additional_data)
        return data_item

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
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
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
        csv_data = [self._csv_data_from_json(d) for d in self.data]
        column_names = [] if not csv_data else [x[0] for x in csv_data[0]]

        with closing(CSVWriter(self._format_and_return_file_path('csv'), column_names)) as csv_file:
            csv_file.writerows(map(dict, csv_data))

    def _csv_data_from_json(self, json_data):
        '''
        Returns a list of tuples of (csv_heading, value) in the same order as supplied in
        self._csv_heading_order.  If the value contains any lists, will extend multiple tuples
        padded to the max length of the list.
        Ex: if the max length of any Category is 2:
        {'Categories': ['a', 'b']} -> [('Categories 1', 'a'), ('Categories 2', 'b')] and
        {'Categories': ['a']} -> [('Categories 1', 'a'), ('Categories 2', '')]
        json_data:  Dictionary of json_names to values.
        '''
        csv_data = []
        for json_name in self._csv_heading_order():
            if json_name not in self._json_keys_that_exist:
                continue
            value = json_data.get(json_name, [])
            csv_data.extend(self._csv_cols_from(json_name, value) or [(json_name, value)])
        return csv_data

    def _send_to_splunk(self):
        common_data = {
            'time': time.time(),
            'host': _hostname_from_env() or socket.gethostname(),
            'index': SPLUNK_REPORT_INDEX,
            'source': self._source,
            'sourcetype': '_json'
        }
        events = [{'event': x} for x in self.data]
        for event in events:
            event.update(common_data)
        response = requests.post(SPLUNK_COLLECTOR_URL, data=' '.join(map(json.dumps, events)),
                                 headers={'Authorization': self._splunk_token},
                                 verify=False)
        response.raise_for_status()


class CoverageReport(ReportWriter):
    base_file_name = COVERAGE_REPORT_FILE
    _source = SPLUNK_COVERAGE_INDEX

    def _csv_heading_order(self):
        '''The base non extended order of the csv columns for the Coverage Report'''
        coverage_list = ['Feature Name', 'Test Name', 'Polarity', 'Priority', 'Suite', 'Status',
                         'Execution Method']
        return (super(CoverageReport, self)._csv_heading_order() + coverage_list +
                JIRA_STATUS_DISPLAY_NAMES)

    def _build_test(self, test):
        test_data = {'Test Name': test.name, 'Feature Name': test.feature_name}
        test_data.update({x: y for (x, y) in test.attributes.items() if y})
        test_data.update({x: y for (x, y) in test.jiras.items() if y})
        return self._data_item(**test_data)

    def _data(self):
        return list(map(self._build_test, self.test_group.tests))


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


def run_reports(test_group, business_unit, team, product_name, *report_args, **report_kwargs):
    CoverageReport(test_group, business_unit, team, product_name, *report_args, **report_kwargs)
    test_group.validate()
