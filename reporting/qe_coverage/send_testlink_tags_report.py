#!/usr/bin/env python
'''
Send a TestLink test hierarchy XML export to coverage aggregator.

This tool consumes an XML file exported from TestLink.

The Execution Method defaults to 'manual' unless there is an automated tag (keyword)
for the test case.
'''


import argparse
import json
import os
import sys
from xml.sax import parse
from xml.sax.handler import ContentHandler

from qe_coverage.base import REPORT_PATH, TestGroup, run_reports
from qecommon_tools import display_name


# TODO: As with the other coverage tools, this should come from
#       somewhere else. For now, it's here:
INTERFACE_TYPES = ['api', 'gui']


def _cleanup_categories(categories, leading_categories_to_strip):
    '''
    Filter and trim the categories in to a cleaned up version.

    Empty categories will be removed.
    Categories in the amount of 'leading_categories_to_strip' will be removed
    from front of the categories list.
    '''
    new_categories = [item.strip() for item in categories if item.strip()]
    new_categories = new_categories[leading_categories_to_strip:]
    assert new_categories, 'No categories found when processing: "{}"'.format(categories)
    return new_categories


# When stories were ported over to TestLink from JIRA, they sometimes
# have a prefix that we want to remove:
TC_PREFIX = 'tc:'
TC_PREFIX_LEN = len(TC_PREFIX)


def test_case_name_sanitize(name):
    '''Cleanup formatting of test names.'''
    if name.lower().startswith(TC_PREFIX):
        name = name[TC_PREFIX_LEN:]
    return name.strip()


class TestLinkContentHandler(ContentHandler):
    '''Process TestLink XML file.

    NOTE: keyword element's name is what we call 'tag' in the coverage reporting.
    '''

    def __init__(self, leading_categories_to_strip):
        ContentHandler.__init__(self)  # super() does not work on this class. :-(
        self.leading_categories_to_strip = leading_categories_to_strip

    def startDocument(self):  # noqa: N802
        self.categories = []
        self.testcase = None
        self.tests = TestGroup()

    def start_testsuite(self, attrs):
        suite_name = attrs.get('name')
        self.categories.append(suite_name)

    def end_testsuite(self):
        assert self.categories, 'Ended more test suites than were started'
        self.categories.pop()

    def start_testcase(self, attrs):
        assert not self.testcase, 'test cases should not be nested!'
        self.testcase = test_case_name_sanitize(attrs.get('name'))
        self.tags = []

    def end_testcase(self):
        assert self.testcase, 'ended a test case but not in one'
        categories = _cleanup_categories(self.categories, self.leading_categories_to_strip)
        # Workaround: See https://jira.rax.io/browse/QET-26 Default to manual, not automated.
        if 'automated' not in self.tags:
            self.tags.append('manual')
        self.tests.add(name=self.testcase, categories=categories,
                       tags=self.tags)
        self.testcase = None
        self.tags = None  # Cannot append to none, leave poison pill in case.

    def start_keyword(self, attrs):
        assert self.testcase, 'Keyword found outside of test case'
        self.tags.append(attrs.get('name'))

    def startElement(self, element, attrs):  # noqa: N802
        helper = getattr(self, 'start_{}'.format(element.lower()), None)
        if callable(helper):
            helper(attrs)

    def endElement(self, element):  # noqa: N802
        helper = getattr(self, 'end_{}'.format(element.lower()), None)
        if callable(helper):
            helper()


def testlink_xml_to_test_group(xml_file_name, leading_categories_to_strip):
    '''
    Returns a TestGroup containing all the test data from xml_file_name.
    '''
    content = TestLinkContentHandler(leading_categories_to_strip)
    parse(xml_file_name, content)
    return content.tests


def main():
    parser = argparse.ArgumentParser(description='Test Reports')
    parser.add_argument('testlink_xml_file',
                        help='The name of the exported testlink xml file to process')
    # NOTE: This is a temporary work-around, TestLink structure is such that multiple
    #       product test suites can be present together, the reporting code needs to be expanded
    #       to handle that use case. QGTM-671 is tracking this.
    parser.add_argument('product_name',
                        help='The name of the product')
    parser.add_argument('default_interface_type', choices=INTERFACE_TYPES,
                        help='The interface type of the product '
                             'if it is not otherwise specified or in the category list')
    parser.add_argument('-o', '--output-dir', default=REPORT_PATH,
                        help='Output directory for the generated report files.')
    parser.add_argument('--leading-categories-to-strip', type=int, default=0,
                        help='The number of leading categories to omit from the coverage data '
                             'sent to Splunk')
    parser.add_argument('--dry-run', action='store_true',
                        help='Do not generate reports or upload; only validate the tags.')
    args = parser.parse_args()

    test_group = testlink_xml_to_test_group(args.testlink_xml_file,
                                            args.leading_categories_to_strip)
    if args.dry_run:
        sys.exit(test_group.validate())

    run_reports(test_group, args.product_name, args.default_interface_type, args.output_dir)


if __name__ == '__main__':
    main()
