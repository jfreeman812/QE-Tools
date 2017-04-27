#!/usr/bin/env python
import argparse
import fnmatch
import functools
import itertools
import os.path
import re
import string

import behave.parser
import sphinx
import sphinx.util

SOURCE_PATTERNS = ('*.feature', '*.md', '*.rst')


def rst_escape(unescaped):
    '''Escape reST-ful characters to prevent parsing errors.'''
    return unescaped.replace('*', '\*')


def _get_source_files(files):
    filter_partial = functools.partial(fnmatch.filter, files)
    return list(itertools.chain(*map(filter_partial, SOURCE_PATTERNS)))


class ParseBase(object):
    sections = ['', '=', '-', '~', '.', '*', '+', '_', '<', '>', '/']

    def __init__(self, dest_prefix, args):
        self.dest_prefix = dest_prefix
        self.args = args
        self.dest_suffix = args.suffix
        self._output = []

    def add_output(self, line, line_breaks=1):
        self._output.append('{}{}'.format(line, '\n' * line_breaks))

    def blank_line(self):
        self.add_output('')

    def create_section(self, level, section):
        '''Create a section of <level> (1-10 supported).'''
        self.add_output(section)
        self.add_output(self.sections[level] * len(section.rstrip()),
                        line_breaks=2)

    def write_file(self):
        '''Write the output file for project/category <name>.'''
        file_name = os.extsep.join([self.dest_prefix, self.dest_suffix])
        file_path = os.path.join(self.args.output_path, file_name)
        if self.args.dry_run:
            print('Would create file [{}]'.format(file_path))
            return
        if not self.args.force and os.path.isfile(file_path):
            print('File {} already exists, skipping.'.format(file_path))
            return
        if not self.args.quiet:
            print('Creating file [{}]'.format(file_path))
        with sphinx.util.osutil.FileAvoidWrite(file_path) as f:
            f.write(''.join(self._output))


class ParseSource(ParseBase):
    def __init__(self, source_path, category, args):
        self.source_path = source_path
        source_name = os.path.basename(source_path)
        source_prefix, self.source_suffix = os.path.splitext(source_name)
        dest_prefix = '.'.join([category, source_prefix])
        super().__init__(dest_prefix, args)

    def update_suffix(self):
        self.dest_suffix = self.source_suffix.lstrip(os.extsep)

    def section(self, level, obj):
        section_name = '{}: {}'.format(obj.keyword, obj.name).rstrip(': ')
        self.create_section(level, section_name)

    def description(self, description):
        if description:
            if not isinstance(description, (list, tuple)):
                description = [description]
            self.add_output('.. pull-quote::', line_breaks=2)
            self.add_output('   {}'.format('\n   '.join(description)),
                            line_breaks=2)

    def tags(self, tags):
        if tags:
            self.add_output('.. admonition:: Tagged')
            self.add_output('   :class: note', line_breaks=2)
            self.add_output('   {}'.format(', '.join(tags)), line_breaks=2)

    def steps(self, steps):
        for step in steps:
            bold_step = re.sub(r'(\<.*?\>)', r'**\1**', rst_escape(step.name))
            self.add_output('- {} {}'.format(step.keyword, bold_step))
            if step.table:
                self.table(step, inline=True)
            if step.text:
                self.description(step.text)
        self.blank_line()

    def examples(self, examples):
        for example in examples:
            self.table(example)

    def table(self, obj, inline=False):
        spacing = '   ' if inline else ''
        if inline:
            # When inline, add a new line to separate it from the inline
            # content because it causes problems for the reST converter
            self.blank_line()
        directive = '.. csv-table::'
        if not inline:
            directive += ' {}: {}'.format(obj.keyword, obj.name)
        self.add_output('{}{}'.format(spacing, directive))
        headers = '", "'.join(obj.table.headings)
        self.add_output('{}   :header: "{}"'.format(spacing, headers),
                        line_breaks=2)
        for row in obj.table.rows:
            row = (rst_escape(item.strip('"')) for item in row)
            self.add_output('{}   "{}"'.format(spacing, '", "'.join(row)))
        if not inline:
            # If not inline, seprarate the directive from additional content
            self.blank_line()

    def _set_output(self):
        self.update_suffix()
        with open(self.source_path, 'r') as source_fo:
            self._output = source_fo.readlines()

    def parse(self):
        '''Build the text of the file and write the file.'''
        if not fnmatch.fnmatch(self.source_path, SOURCE_PATTERNS[0]):
            return self._set_output()
        try:
            feature = behave.parser.parse_file(self.source_path)
            self.section(1, feature)
            self.tags(feature.tags)
            self.description(feature.description)
            if feature.background:
                self.section(2, feature.background)
                self.steps(feature.background.steps)
            for scenario in feature.scenarios:
                self.section(2, scenario)
                self.tags(scenario.tags)
                self.description(scenario.description)
                self.steps(scenario.steps)
                self.examples(getattr(scenario, 'examples', []))
        except behave.parser.ParserError:
            self._set_output()


class ParseTOC(ParseBase):
    def parse(self, feature_set, section=None):
        self.create_section(1, section or self.args.doc_project)
        self.add_output('.. toctree::')
        self.add_output('   :maxdepth: {}'.format(self.args.maxdepth),
                        line_breaks=2)
        prev_feature = ''
        for feature in sorted(feature_set):
            # look if the feature is a sub-category and, if yes, ignore it
            if feature.startswith('{}.'.format(prev_feature)):
                continue
            prev_feature = feature
            self.add_output('   {}'.format(feature))


def _path_to_category(walk_root, root_path):
    category_dir = os.path.dirname(root_path)
    return os.path.relpath(walk_root, category_dir).replace(os.path.sep, '.')


class RecurseTree(object):
    def __init__(self, args):
        self.root_path = args.gherkin_path
        self.args = args

    def _is_included(self, file_path):
        '''Determine if a file or path should be included based on
           exclude_patterns and private'''
        if os.path.basename(file_path).startswith('_') and not self.args.private:
            return False
        return not any(map(lambda x: fnmatch.fnmatch(file_path, x),
                           self.args.exclude_patterns))

    def _filter_categories(self, root, categories):
        categories = [x for x in categories if self._is_included(os.path.join(root, x))]
        for category in categories[:]:
            category_files = os.listdir(os.path.join(root, category))
            if not _get_source_files(category_files):
                categories.remove(category)
        return categories

    def _build_name(self, root, project, category):
        package = root[len(self.root_path):].lstrip(os.path.sep).replace(os.path.sep, '.')
        return '.'.join(filter(None, [project, package, category]))

    def _display_name(self, category_name, root, category):
        name_path = os.path.join(root, category, 'display_name.txt')
        if os.path.exists(name_path):
            with open(name_path, 'r') as name_fo:
                return name_fo.read().rstrip('\r\n')
        return string.capwords(category_name.split('.')[-1].replace('_', ' '))

    def _parse_category(self, root, project, category):
        category_name = self._build_name(root, project, category)
        category_path = os.path.join(root, category)

        name_partial = functools.partial(str.format, '{}.{}', category_name)
        category_files = list(map(name_partial, os.listdir(category_path)))

        category_map = map(lambda x: os.path.splitext(x)[0],
                           _get_source_files(category_files))

        display_name = self._display_name(category_name, root, category)
        # Each parsed category needs a TOC for sphinx so we write it here
        toc_file = ParseTOC(category_name, self.args)
        toc_file.parse(category_map, section=display_name)
        toc_file.write_file()
        return category_name

    def parse(self):
        feature_set = set()
        project = os.path.basename(self.root_path)
        walk = sphinx.util.osutil.walk
        for out in walk(self.root_path, followlinks=self.args.follow_links):
            root, categories, files = out
            base_category = _path_to_category(root, self.root_path)
            source_files = _get_source_files(files)
            path_partial = functools.partial(os.path.join, root)
            source_paths = sorted(filter(self._is_included, map(path_partial,
                                                                source_files)))
            for category in self._filter_categories(root, categories):
                feature_set.add(self._parse_category(root, project, category))
            for source_path in source_paths:
                feature = ParseSource(source_path, base_category, self.args)
                feature.parse()
                feature.write_file()
                if root == self.root_path:
                    feature_set.add(feature.dest_prefix)
        return feature_set


def main():
    description = 'Look recursively in <gherkin_path> for Gherkin files and READMEs create one ' \
                  'reST file for each.'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('gherkin_path', help='Directory to search for Gherkin files')
    parser.add_argument('output_path', help='Directory to place all output')
    parser.add_argument('exclude_patterns', nargs='*',
                        help='file and/or directory patterns that will be excluded')
    parser.add_argument('-d', '--maxdepth', type=int, default=4,
                        help='Maximum depth of submodules to show in the TOC')
    parser.add_argument('-f', '--force', action='store_true', help='Overwrite existing files')
    parser.add_argument('-l', '--follow-links', action='store_true', help='Follow symbolic links.')
    parser.add_argument('-n', '--dry-run', action='store_true',
                        help='Run the script without creating files')
    parser.add_argument('-e', '--separate', action='store_true',
                        help='Put documentation for each module on its own page')
    parser.add_argument('-P', '--private', action='store_true', help='Include "_private" folders')
    parser.add_argument('-T', '--no-toc', action='store_true',
                        help='Don\'t create a table of contents file')
    parser.add_argument('-N', '--toc-name', help='File name for TOC')
    parser.add_argument('-s', '--suffix', help='file suffix (default: rst)', default='rst')
    parser.add_argument('-H', '--doc-project', help='Project name (default: root module name)')
    parser.add_argument('-q', '--quiet', action='store_true', help='Silence any output to screen')
    parser.add_argument('--version', action='store_true', help='Show version information and exit')
    args = parser.parse_args()
    if args.version:
        parser.exit(message='Sphinx (sphinx-apidoc) {}'.format(sphinx.__display_version__))
    if args.doc_project is None:
        args.doc_project = os.path.abspath(args.gherkin_path).split(os.path.sep)[-1]
    args.suffix.lstrip(os.extsep)
    args.gherkin_path = os.path.abspath(args.gherkin_path)
    args.output_path = os.path.abspath(args.output_path)
    if not os.path.isdir(args.gherkin_path):
        parser.error('{} is not a directory.'.format(args.gherkin_path))
    if not os.path.isdir(args.output_path):
        if not args.dry_run:
            os.makedirs(args.output_path)
    args.exclude_patterns = [os.path.abspath(exclude) for exclude in args.exclude_patterns]
    tree = RecurseTree(args)
    feature_set = tree.parse()
    if not args.no_toc:
        toc_file = ParseTOC(args.toc_name or 'features', args)
        toc_file.parse(feature_set)
        toc_file.write_file()


if __name__ == '__main__':
    main()
