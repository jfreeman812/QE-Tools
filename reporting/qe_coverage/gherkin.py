import argparse
import fnmatch
import os
import sys
from tempfile import mkdtemp

import attr
import behave.parser

from qe_coverage.base import TestGroup, run_reports, update_parser, coverage_tables
from qecommon_tools import cleanup_and_exit, display_name


# Any display name in nuisance_category_names will be omitted from the categories. 'features' is
# ignored as it is a special name required in cucumber and meaningless for reporting.
NUISANCE_CATEGORY_NAMES = ['features', '.']
all_tags = [
    t.tag for table in [coverage_tables[tab] for tab in coverage_tables.tables[1:]]
    for t in table if t.tag != ''
]


@attr.s
class ParseProject(object):
    project_path = attr.ib()
    leading_categories_to_strip = attr.ib(type=int, default=0)
    search_hidden = attr.ib(type=bool, default=False)
    exclude_patterns = attr.ib(default=attr.Factory(list))

    def _feature_for(self, file_path):
        '''Create a behave feature object and attach the relative path of the feature file.'''
        feature = behave.parser.parse_file(file_path)
        feature.relative_path = os.path.relpath(os.path.dirname(file_path), self.project_path)
        return feature

    def _build_categories(self, relative_path):
        '''
        Returns a list of categories for the relative_path supplied. Categories are created by
        splitting the grouping name apart and turning each piece into a display name.  The highest
        level of the directory is returned as the first item, and the lowest level as the last.
        Ex:  relative_path = 'parent/sub/lowest' -> ['parent', 'sub', 'lowest']
        '''
        full_path = self.project_path
        categories = []
        for category in os.path.normpath(relative_path).split(os.sep):
            full_path = os.path.join(full_path, category)
            name = display_name(full_path)
            if name.lower() not in NUISANCE_CATEGORY_NAMES:
                categories.append(name)
        return categories[self.leading_categories_to_strip:]

    def _is_included(self, check_path):
        '''Check if a file/dir should be included based on exclude and hidden options'''
        if check_path.startswith('.') and not self.search_hidden:
            return False
        return not any(map(lambda x: fnmatch.fnmatch(check_path, x), self.exclude_patterns))

    def _normalize_tag(self, tag):
        if tag not in all_tags:
            for expected_tag in all_tags:
                if tag.startswith('{}-'.format(expected_tag)):
                    return expected_tag
        return tag

    def _normalize_tags(self, tags):
        return list(map(self._normalize_tag, tags))

    def build_coverage(self):
        '''
        Returns a list of TestCoverage objects created by walking a product base directory for any
        feature files and parsing them into TestCoverage objects.
        '''
        tests = TestGroup()
        for dir_path, dir_names, file_names in os.walk(self.project_path):
            # If items are removed from dir_names, os.walk will not search them.
            dir_names[:] = list(filter(self._is_included, dir_names))
            for file_name in fnmatch.filter(file_names, '*.feature'):
                file_path = os.path.join(dir_path, file_name)
                feature = self._feature_for(file_path)
                categories = self._build_categories(feature.relative_path)
                for test in feature.walk_scenarios():
                    if not categories or test.feature.name != categories[-1]:
                        # Only add the feature name if it doesn't match the last category
                        categories.append(test.feature.name)
                    tests.add(name=test.name, categories=categories,
                              tags=self._normalize_tags(test.tags),
                              parent_tags=test.feature.tags, file_path=file_path)
        return tests


def run_gherkin_reports(product_dir, *args, **kwargs):
    leading_categories_to_strip = kwargs.pop('leading_categories_to_strip', 0)
    project = ParseProject(os.path.join(os.getcwd(), product_dir),
                           leading_categories_to_strip=leading_categories_to_strip,
                           search_hidden=kwargs.pop('search_hidden', False),
                           exclude_patterns=kwargs.pop('exclude_patterns', None) or [])
    test_list = project.build_coverage()
    run_reports(test_list, *args, **kwargs)


def main():
    epilog = 'Note: Run this script from the root of the test tree being reported on'
    parser = argparse.ArgumentParser(description='Collect and publish Gherkin coverage report',
                                     epilog=epilog)
    parser = update_parser(parser)
    product_help = 'The director(ies) to start looking for feature files. Useful when cloning a '\
                   'repository and the feature files are stored in a sub folder.'
    parser.add_argument('-p', '--product_dir', nargs='?', default='', help=product_help)
    parser.add_argument('--search_hidden', action='store_true', help='Include ".hidden" folders')
    parser.add_argument('--exclude', dest='exclude_patterns', action='append',
                        help='file and/or directory patterns that will be excluded')
    product_kwargs = vars(parser.parse_args())
    run_gherkin_reports(product_kwargs.pop('product_dir'), product_kwargs.pop('product_hierarchy'),
                        product_kwargs.pop('default_interface_type'), **product_kwargs)


if __name__ == '__main__':
    main()
