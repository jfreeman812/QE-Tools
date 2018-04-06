#!/usr/bin/env python
'''
Send a TestLink test hierarchy XML export to coverage aggregator.

This tool consumes an XML file exported from TestLink.

The Execution Method defaults to 'manual' unless there is an automated tag (keyword)
for the test case.
'''

from __future__ import print_function

import argparse
import json
import os
import sys
from tempfile import mkdtemp
from xml.sax import parse
from xml.sax.handler import ContentHandler

from qe_coverage.base import TestGroup, update_parser, run_reports
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


def neuter_unicode(thing):
    return thing and thing.encode('ascii', 'xmlcharrefreplace')


def test_case_name_sanitize(name):
    '''Cleanup formatting of test names.'''
    name = neuter_unicode(name)
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

    def setDocumentLocator(self, locator):  # noqa: N802
        self.locator = locator

    def startDocument(self):  # noqa: N802
        self.categories = []
        self.testcase = None
        self.last_testcase = '<No Test Case processed yet>'
        self.tests = TestGroup()

    def start_testsuite(self, attrs):
        suite_name = neuter_unicode(attrs.get('name'))
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
        # TestLink data doesn't come from a file system with hierarchical
        # file names, so pass in file_path as the TestLink categories path
        # to make it easier for humans to find the test if/when an error
        # report is generated.
        self.tests.add(name=self.testcase, categories=categories,
                       tags=self.tags, file_path=':'.join(self.categories))
        self.last_testcase = self.testcase
        self.testcase = None
        self.tags = None  # Cannot append to none, leave poison pill in case.

    def start_keyword(self, attrs):
        name = neuter_unicode(attrs.get('name'))
        if not self.testcase:
            # NOTE: Experiments with the GSCS QE TestLink data shows that the
            # locator line-number by itself isn't accurate for reasons still TBD,
            # so print the name of the last test case seen before the problem,
            # which helps human reader of the XML to find out where the errant keyword is.
            msg = 'Warning: Line {}: Ignoring keyword "{}" found outside of test case, after {}'
            print(msg.format(self.locator.getLineNumber(), name, self.last_testcase))
            return
        self.tags.append(name)

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


def run_testlink_reports(testlink_xml_file, *args, **kwargs):
    test_group = testlink_xml_to_test_group(testlink_xml_file,
                                            kwargs.get('leading_categories_to_strip'))
    run_reports(test_group, *args, **kwargs)


def main():
    parser = argparse.ArgumentParser(description='Create and publish TestLink coverage report')
    parser.add_argument('testlink_xml_file',
                        help='The name of the exported testlink xml file to process')
    parser = update_parser(parser)
    kwargs = vars(parser.parse_args())
    run_testlink_reports(kwargs.pop('testlink_xml_file'), kwargs.pop('product_hierarchy'),
                         kwargs.pop('default_interface_type'), **kwargs)


if __name__ == '__main__':
    main()
