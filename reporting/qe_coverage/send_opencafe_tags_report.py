#!/usr/bin/env python
'''
Send a tags-based OpenCAFE test coverage report to splunk.

This tool consumes a JSON file produced by a tags-harvesting run of OpenCAFE.
The test repo is expected to have the following general structure, as reflected
by the data in the tags JSON file.

For repos with other structures, it might be this tool can be adapted,
or perhaps just used as a model for other tools.

The repo is expected to have two top-level directories:
<something>cafe
<something>roast

Somewhere in the "roast" tree, there can be a directory named "api" or "gui" or "ui"
to indicate the kind of interface being tested by the tests under that part of the directory tree.
For any test which does _not_ have a tag to set its interface_type:
* If it is under one of the directories named above,
  that directory determines the interface_type for the test.
* If it is not under of the directories named above,
  the command line parameter to this tool will be used for that test's interface_type.

The very last entry of the provenence list (explain that term!) will be used
as the feature name for the test (and removed from the categories list).

The test's reported categories will be based on the directory heirachy,
as modified and filtered per above descriptions.

IDEALY the Product name would be the first non-filtered name in the hierarchy,
but for now the product name has to be specified on the command line parameter
due to tooling limitations. Fixing this is captured in Jira QGTM-671.
'''


import argparse
import fnmatch
import json
import os
import re
import sys

from qe_coverage.base import REPORT_PATH, TestGroup, update_parser, run_reports
from qecommon_tools import display_name


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


def coverage_json_to_test_group(coverage_file_name, default_interface_type,
                                leading_categories_to_strip):
    '''
    Returns a TestGroup containing all the test data from the coverage file.

    Where any test data doesn't contain interface information,
    use default_interface_type.
    '''
    tests = TestGroup()
    with open(coverage_file_name) as json_lines:
        for line in json_lines.readlines():
            test_data = json.loads(line)
            categories, interface = _parse_provenance(test_data['provenance'],
                                                      default_interface_type,
                                                      leading_categories_to_strip)
            feature_name = categories.pop()
            tests.add(name=test_data['test'], categories=categories, tags=test_data['tags'],
                      feature_name=feature_name)

    return tests


def run_opencafe_reports(coverage_json_file, *args, **kwargs):
    test_group = coverage_json_to_test_group(coverage_json_file, args[0],
                                             kwargs.get('leading_categories_to_strip'))
    run_reports(test_group, *args, **kwargs)


def main():
    parser = argparse.ArgumentParser(description='Send OpenCAFE coverage report')
    parser.add_argument('coverage_json_file',
                        help='The name of the coverage json file to process')
    parser = update_parser(parser)
    kwargs = vars(parser.parse_args())
    run_opencafe_reports(kwargs.pop('coverage_json_file'), kwargs.pop('product_hierarchy'),
                         kwargs.pop('default_interface_type'), **kwargs)


if __name__ == '__main__':
    main()
