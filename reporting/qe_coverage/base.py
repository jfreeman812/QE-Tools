#!/usr/bin/env python
from __future__ import print_function
import argparse
from collections import defaultdict, namedtuple
from contextlib import closing
import csv
import datetime
from itertools import chain
import json
import os
import re
import socket
import sys
import tempfile
import time  # Needed because Python 2.7 doesn't support datetime.datetime.now().timestamp()
try:
    from urllib import parse
except ImportError:
    import urlparse as parse

import attr
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from tableread import SimpleRSTReader

from qecommon_tools import cleanup_and_exit, padded_list
from qecommon_tools.http_helpers import validate_response_status_code


# Silence requests complaining about insecure connections; needed for our internal certificates
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


NO_STATUS_TICKET_KEY = 'Tickets'
HIERARCHY_DELIMITER = '::'
HIERARCHY_FORMAT = '<TEAM_NAME>{}<PRODUCT_NAME>'.format(HIERARCHY_DELIMITER)
TAG_DEFINITION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'coverage.rst')
COVERAGE_REPORT_FILE = '{product_name}_coverage_report_{time_stamp}.{ext}'
TICKET_RE = re.compile('([A-Z][A-Z]+-?[0-9]+)')
COVERAGE_URL_TEMPLATE = 'https://qetools.rax.io/coverage/{}'
COVERAGE_STAGING_URL = COVERAGE_URL_TEMPLATE.format('staging')
COVERAGE_PRODUCTION_URL = COVERAGE_URL_TEMPLATE.format('production')

####################################################################################################
# Globals
####################################################################################################
coverage_tables = SimpleRSTReader(TAG_DEFINITION_FILE)
status_table = coverage_tables['Status'].exclude_by(tag='')
TICKET_STATUS_DISPLAY_NAMES = [NO_STATUS_TICKET_KEY] + sorted(status_table.get_fields('report_as'))


@attr.s
class TestCoverage(object):
    name = attr.ib()
    categories = attr.ib(default=attr.Factory(list))
    tags = attr.ib(default=attr.Factory(list))
    parent_tags = attr.ib(default=attr.Factory(list))
    file_path = attr.ib(default='')
    # Pre-defined Constants
    tickets = attr.ib(default=attr.Factory(lambda: defaultdict(list)), init=False)
    attributes = attr.ib(default=attr.Factory(dict), init=False)
    errors = attr.ib(default=attr.Factory(list), init=False)

    def build(self):
        '''Build the necessary objects from the provided tag list(s).'''
        self.organize_prescriptives()
        self.organize_structureds()
        self.organize_tickets()

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
            message = '{}:{}:Multiple tags for prescriptive attribute {} ({})'
            self.errors.append(message.format(self.file_path, self.name, attribute, found_tags))
        if not found_tags and not default_value:
            message = '{}:{}:No tag for prescriptive attribute {}. Must be one of {}'
            self.errors.append(message.format(self.file_path, self.name, attribute, valid_tags))
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
            message = '{}:{}:There can only be one category tag per test'
            self.errors.append(message.format(self.file_path, self.name))
        self.attributes['Categories'] = tag_categories[0] if tag_categories else self.categories
        self.attributes['Projects'] = self.structured_tag('project')

    def organize_tickets(self):
        for tag_list in (self.tags, self.parent_tags):
            self._organize_tickets(tag_list)
        for status in (x for x in self.tickets if not self.tickets[x]):
            message = '{}:{}:Ticket ID not found for status "{}"'
            self.errors.append(message.format(self.file_path, self.name, status))

    def _organize_tickets(self, tag_list):
        '''
        Iterate over all provided tags and update the tickets variables. If the ticket is
        associated with a status tag, that status will be the key; otherwise the key will be
        'Tickets'.
        '''
        status = None
        for tag in tag_list:
            if tag in status_table.get_fields('tag'):
                status = status_table.matches_all(tag=tag).data[0].report_as
                # Since a status with an empty list indicates that no tickets were associated with
                # that status, we need to explicity create the status key with the default value
                # for validation later.
                self.tickets[status]
                continue
            if TICKET_RE.match(tag):
                self.tickets[status or NO_STATUS_TICKET_KEY].append(tag)
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

    def add(self, name, categories=None, tags=None, parent_tags=None,
            file_path=''):
        test = TestCoverage(name=name, categories=categories, tags=tags,
                            parent_tags=parent_tags or [], file_path=file_path)
        test.build()
        self.tests.append(test)
        self.errors.extend(test.errors)

    def validate(self):
        if self.errors:
            print('\n'.join(self.errors), file=sys.stderr)
        return len(self.errors)


####################################################################################################
# Report Generation
####################################################################################################


def _empty_str_padded_list(list_or_none, pad_to_length):
    '''
    Returns a padded list of a length defined by pad_to_length, the padding will be an empty string.
    '''
    list_to_pad = list_or_none or []
    return padded_list(list_to_pad, pad_to_length, '')


def _product_hierarchy_as_list(product_hierarchy):
    return product_hierarchy.lower().replace(' ', '_').split(HIERARCHY_DELIMITER)


class ReportWriter(object):
    base_file_name = ''

    def __init__(self, test_group, product_hierarchy, interface_type, output_dir='',
                 preserve_files=False, timestamp=None, production_endpoint=False, **_):
        self.test_group = test_group
        self.product_hierarchy = product_hierarchy
        self.interface_type = interface_type
        self.output_dir = output_dir or tempfile.mkdtemp()
        self.preserve_files = preserve_files
        self.timestamp = timestamp
        self.production_endpoint = production_endpoint
        self._max_lens = {}
        self.data = self._data()
        self._json_keys_that_exist = {k for d in self.data for k in d.keys()}

    def write_report(self):
        self._write_json_report()
        self._write_csv_report()
        if self.preserve_files:
            print('Generated files located at: {}'.format(self.output_dir))

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
            'Product Hierarchy',
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
        data_item = {'Product Hierarchy': self.product_hierarchy,
                     'Interface Type': self.interface_type}
        data_item.update(additional_data)
        return data_item

    def _data(self):
        '''
        This method should be overridden to return a list of dictionaries containing reporting data
        '''
        raise NotImplementedError('_data method must be overridden')

    def _format_file_name(self, extension):
        '''Create the file name based on the product name, current timestamp, and extension'''
        format_kwargs = {
            'product_name': _product_hierarchy_as_list(self.product_hierarchy)[-1],
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

    def send_report(self):
        params = {'timestamp': self.timestamp} if self.timestamp else {}
        coverage_url = COVERAGE_PRODUCTION_URL if self.production_endpoint else COVERAGE_STAGING_URL
        response = requests.post(coverage_url, json=self.data, params=params, verify=False)
        validate_response_status_code('CREATED', response)
        return response.json().get('url', '')


class CoverageReport(ReportWriter):
    base_file_name = COVERAGE_REPORT_FILE

    def _csv_heading_order(self):
        '''The base non extended order of the csv columns for the Coverage Report'''
        coverage_list = ['Test Name', 'Polarity', 'Priority', 'Suite', 'Status', 'Execution Method']
        return (super(CoverageReport, self)._csv_heading_order() + coverage_list +
                TICKET_STATUS_DISPLAY_NAMES)

    def _build_test(self, test):
        test_data = {'Test Name': test.name}
        test_data.update({x: y for (x, y) in test.attributes.items() if y})
        test_data.update({x: y for (x, y) in test.tickets.items() if y})
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


def run_reports(test_group, *args, **kwargs):
    report = CoverageReport(test_group, *args, **kwargs)
    report.write_report()
    status = 0 if kwargs.get('validate') is False else test_group.validate()
    if not kwargs.get('dry_run'):
        print(report.send_report())
        status = 0
    cleanup_and_exit(dir_name='' if report.preserve_files else report.output_dir, status=status)


def product_hierarchy(string):
    if len(_product_hierarchy_as_list(string)) != 2:
        message = 'product_hierarchy must be formatted {}'.format(HIERARCHY_FORMAT)
        raise argparse.ArgumentTypeError(message)
    return string


def update_parser(parser):
    parser.add_argument('default_interface_type', choices='gui api'.split(),
                        help='The interface type of the product if it is not otherwise specified')
    # NOTE: This is a temporary work-around, each coverage file's line has a product available,
    #       but since we have multiple products right now, the reporting code needs to be expanded
    #       to handle that use case. QET-22 is tracking this.
    parser.add_argument('product_hierarchy', type=product_hierarchy,
                        help='Product hierarchy, formatted {}'.format(HIERARCHY_FORMAT))
    parser.add_argument('--preserve-files', default=False, action='store_true',
                        help='Preserve report files generated')
    parser.add_argument('--dry-run', action='store_true',
                        help='Do not generate reports or upload; only validate the tags.')
    parser.add_argument('--leading-categories-to-strip', type=int, default=0,
                        help='The number of leading categories to omit from the coverage data JSON')
    parser.add_argument('--timestamp', default=None,
                        help='Unix Timestamp for representative date of the data')
    parser.add_argument('--output-dir', default=None, help=argparse.SUPPRESS)
    parser.add_argument('--no-validate', dest='validate', action='store_false',
                        help='write reports without validating data')
    parser.add_argument('--production-endpoint', action='store_true',
                        help='Send coverage data to the production endpoint')
    return parser
