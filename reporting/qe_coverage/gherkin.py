import fnmatch
import os
import sys
from tempfile import mkdtemp

import attr
import behave.parser

from qe_coverage.base import TestGroup, run_reports, build_parser
from qecommon_tools import cleanup_and_exit, display_name


# Any display name in nuisance_category_names will be omitted from the categories. 'features' is
# ignored as it is a special name required in cucumber and meaningless for reporting.
NUISANCE_CATEGORY_NAMES = ['features']


@attr.s
class ParseProject(object):
    project_path = attr.ib()

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
        return categories

    def build_coverage(self, search_hidden=False):
        '''
        Returns a list of TestCoverage objects created by walking a product base directory for any
        feature files and parsing them into TestCoverage objects.
        '''
        tests = TestGroup()
        for dir_path, dir_names, file_names in os.walk(self.project_path):
            if not search_hidden:
                # If items are removed from dir_names, os.walk will not search them.
                dir_names[:] = [x for x in dir_names if not x.startswith('.')]
            for file_name in fnmatch.filter(file_names, '*.feature'):
                file_path = os.path.join(dir_path, file_name)
                feature = self._feature_for(file_path)
                categories = self._build_categories(feature.relative_path)
                for test in feature.walk_scenarios():
                    tests.add(name=test.name, categories=categories, tags=test.tags,
                              feature_name=test.feature.name, parent_tags=test.feature.tags,
                              file_path=file_path)
        return tests

    @property
    def name(self):
        return display_name(os.path.normpath(self.project_path))


def run_gherkin_reports(product_dir, *report_args, **product_kwargs):
    project = ParseProject(os.path.join(os.getcwd(), product_dir))
    test_list = project.build_coverage(search_hidden=product_kwargs.pop('search_hidden', False))
    if product_kwargs.pop('dry_run'):
        sys.exit(test_list.validate())
    else:
        run_reports(test_list, project.name, *report_args, **product_kwargs)


def main():
    parser = build_parser('Collect and publish Gherkin coverage report')
    product_help = 'The director(ies) to start looking for feature files. Useful when cloning a '\
                   'repository and the feature files are stored in a sub folder.'
    parser.add_argument('-p', '--product_dir', nargs='?', default='', help=product_help)
    parser.add_argument('--search_hidden', action='store_true', help='Include ".hidden" folders')
    args = parser.parse_args()
    output_path = mkdtemp()
    run_gherkin_reports(args.product_dir, args.default_interface_type, output_path,
                        search_hidden=args.search_hidden, dry_run=args.dry_run, host=args.host)
    if not args.preserve_files:
        cleanup_and_exit(dir_name=output_path)
    print('Generated files located at: {}'.format(output_path))


if __name__ == '__main__':
    main()
