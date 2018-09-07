#!/usr/bin/env python
'''
Send a tags-based OpenCAFE/Unittest test coverage report to splunk.

This tool consumes a JSON file produced by a tags-harvesting run of OpenCAFE or
Unittest. The test repo is expected to have the following general structure, as
reflected by the data in the tags JSON file.

For repos with other structures, it might be this tool can be adapted,
or perhaps just used as a model for other tools.

For OpenCAFE the repo is expected to have two top-level directories:
<something>cafe
<something>roast

Somewhere in the "roast" tree, there can be a directory named "api" or "gui" or "ui"
to indicate the kind of interface being tested by the tests under that part of the directory tree.
For any test which does _not_ have a tag to set its interface_type:
* If it is under one of the directories named above,
  that directory determines the interface_type for the test.
* If it is not under of the directories named above,
  the command line parameter to this tool will be used for that test's interface_type.

The test's reported categories will be based on the directory heirachy,
as modified and filtered per above descriptions.

IDEALY the Product name would be the first non-filtered name in the hierarchy,
but for now the product name has to be specified on the command line parameter
due to tooling limitations. Fixing this is captured in Jira QGTM-671.
'''


import argparse
import csv
import json
import re

from qe_coverage.base import TestGroup, update_parser, run_reports


# Map from a directory name (in the categories hierarchy)
# to the interface type default that will be reported for a test.
INTERFACE_TYPES = dict(api='api', gui='gui', ui='gui')

# Nuisance categories are directories used to organize tests but which
# are not helpful to the coverage reporting process.
NUISANCE_CATEGORY_PATTERNS = [re.compile(pattern, flags=re.IGNORECASE)
                              for pattern in ['.*cafe$', '.*roast$']]


def is_nuisance(item):
    return any((pattern.match(item) for pattern in NUISANCE_CATEGORY_PATTERNS))


def _parse_provenance(provenance, default_interface_type, leading_categories_to_strip):
    '''
    Returns a (categories_list, interface_type) tuple based on provenance.

    Anything matching NUISANCE_CATEGORY_NAMES is removed.
    Anything matching a key in INTERFACE_TYPES is removed and the corresponding value
    is set at the interface_type. If no interface type is found in provenance,
    then the interface_type returned is the default_interface_type.
    If more than one INTERFACE_TYPES key is found, the last one found is used.
    Categories in the amount of 'leading_categories_to_strip' will be removed
    from the categories list.
    '''
    categories = []
    interface = None
    for item in provenance:
        if item in INTERFACE_TYPES:
            interface = INTERFACE_TYPES[item]
            continue
        if is_nuisance(item):
            continue
        categories.append(item)
    categories = categories[leading_categories_to_strip:]
    assert categories, 'No categories found when processing: "{}"'.format(provenance)
    return (categories, interface or default_interface_type)


def _get_test_identifier(test_class_name, test_method_name):
    '''Get a unique test identifier based on the class name and test method name.'''
    return '{}.{}'.format(test_class_name, test_method_name)


def _get_injection_data(data_injection_file_path):
    '''Get injection data from a data injection file.'''
    injection_data = {}

    if data_injection_file_path:
        with open(data_injection_file_path, 'r') as data_injection_file:
            data_injection_csv = csv.reader(data_injection_file)
            for row in data_injection_csv:
                # CSV format of: class_name, test_method_name, tag1, tag2, etc.
                class_name = row[0]
                test_method_name = row[1]
                tags = row[2:]
                identifier = _get_test_identifier(class_name, test_method_name)
                injection_data[identifier] = {
                    'tags': tags
                }

    return injection_data


def coverage_json_to_test_group(coverage_file_name, default_interface_type,
                                leading_categories_to_strip, injection_data):
    '''
    Returns a TestGroup containing all the test data from the coverage file.

    Where any test data doesn't contain interface information,
    use default_interface_type.

    Any injection data provided will be appended to a test's coverage data
    before it is added to the TestGroup.
    '''
    tests = TestGroup('unittest')

    with open(coverage_file_name) as json_lines:
        for line in json_lines.readlines():
            test_data = json.loads(line)
            categories, interface = _parse_provenance(test_data['provenance'],
                                                      default_interface_type,
                                                      leading_categories_to_strip)

            # The class name is the last category as parsed from the provenance
            test_method_name = test_data['test']
            test_class_name = categories[-1]
            test_identifier = _get_test_identifier(test_class_name, test_method_name)

            test_coverage_kwargs = {
                'name': test_method_name,
                'categories': categories,
                'tags': test_data['tags']
            }

            if test_identifier in injection_data:
                for key, value in injection_data[test_identifier].items():
                    test_coverage_kwargs[key] += value

            tests.add(**test_coverage_kwargs)

    return tests


def run_unittest_reports(coverage_json_file, *args, **kwargs):
    injection_data = _get_injection_data(kwargs.get('data_injection_file_path'))
    test_group = coverage_json_to_test_group(coverage_json_file, args[0],
                                             kwargs.get('leading_categories_to_strip'),
                                             injection_data)
    run_reports(test_group, *args, **kwargs)


def main():
    parser = argparse.ArgumentParser(description='Send Unittest/OpenCAFE coverage report')
    parser.add_argument('coverage_json_file',
                        help='The name of the coverage json file to process')
    parser = update_parser(parser)
    kwargs = vars(parser.parse_args())
    run_unittest_reports(kwargs.pop('coverage_json_file'), kwargs.pop('product_hierarchy'),
                         kwargs.pop('default_interface_type'), **kwargs)


if __name__ == '__main__':
    main()
