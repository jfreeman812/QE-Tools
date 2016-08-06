#!/usr/bin/env python
"""
Scan the current directory tree for Gherkin feature files and check their
use of tags against the given tags file. Tags are used to generate a test
coverage report as well.
"""

import argparse
import csv
import os
import sys

from collections import namedtuple

from test_tags import TestTags

DIRECTORY_DEPTH_MAX = 3   # Chosen by Chris DeMattio for his reports.
ERROR_EXIT_CODE = 1

# A line with less than this number of columns is not a properly formed
# examples table line, since tables have to have at least one column of data,
# and one column of data divides the line into 3 sections.
MIN_EXAMPLE_TABLE_COLUMNS = 3

write_csv_row = csv.writer(sys.stdout).writerow

# NOTE: This is not (yet) a general Gherkin file validator/checker,
#       so weirdly formatted Gherkin might slip through.

# default tags file location to the same directory as this script...
_here = os.path.dirname(os.path.abspath(__file__))
tags_file_name = os.path.join(_here, 'tags.md')

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('-r', '--report', default=False, action='store_true',
                    help='generate/print a coverage report')
parser.add_argument('-t', '--tagsfile', type=str, default=tags_file_name,
                    metavar='FILE',
                    help="Specify a different tags file to consult")

args = parser.parse_args()

tags = TestTags(args.tagsfile)

master_tags = set(tags.keys())

group_list = sorted(tags.groups.keys())
csv_header_list = group_list + ['scenario',
                                'feature',
                                'feature file'] + \
                               ['level %d' % (x + 1)
                                for x in range(DIRECTORY_DEPTH_MAX)]


error_log = []


def error(msg, location):
    if location is not None:
        msg = "{}, at: {}".format(msg, location)
    error_log.append(msg)


def print_error_log():
    for msg in error_log:
        print msg


class Location(namedtuple('Location', ['dir_list', 'file_name', 'line_no'])):
    def __str__(self):
        full_path = os.path.join(*(self.dir_list + [self.file_name]))
        return "%s, line: %s" % (full_path, self.line_no)


def tags_from(line, location):
    # we don't have to check for leading '@',
    # those will automatically fail the master tags check
    line = line.split('#', 1)[0]
    tags = set(line.split())
    bad_tags = tags - master_tags
    if bad_tags:
        error("Unsupported tags: {}".format(", ".join(bad_tags)), location)
    return tags


def one_tag_from(have_tags, group, location):
    tag_set = tags.groups[group]
    targets = have_tags & tag_set
    if len(targets) > 1:
        error("Mutually exclusive tags: {}".format(" ".join(targets)),
              location)
    if not targets:
        return tags.group_default.get(group)
    tag = targets.pop()
    return tags.report_names.get(tag, "UNKNOWN TAG: %s" % (tag,))


def summary_from(line):
    return line.split(':', 1)[1].strip()

all_scenarios = []


class Scenario(object):
    def __init__(self, scenario, feature, location, tags):
        self.scenario = scenario
        self.feature = feature
        self.location = location
        self.tags = tags
        self.group = dict()
        self.analyze_tags()

    @staticmethod
    def sort_key(obj):
        # By using location, we keep sort stable if the description changes.
        return obj.location

    def analyze_tags(self):
        for group in tags.groups:
            report_as = one_tag_from(self.tags, group, self.location)
            if report_as is None:
                report_as = "MISSING TAG FOR %s" % (group,)
                error("Missing a tag for group '{}' ({})".format(
                    group, " ".join(tags.groups[group])), self.location)
            self.group[group] = report_as

    def print_stats(self):
        write_csv_row([self.group[x] for x in group_list] +
                      [self.scenario, self.feature, self.location.file_name] +
                      self.location.dir_list)


class ScenarioOutline(Scenario):
    def __init__(self, *args, **kwargs):
        super(ScenarioOutline, self).__init__(*args, **kwargs)

    def new_example_table(self, tags):
        self.seen_examples_table_header_row = False
        self.example_tags = tags

    def add_example(self, columns, location):
        if len(columns) < MIN_EXAMPLE_TABLE_COLUMNS:
            error("Examples table entry has too few columns", location)
            return
        if not self.seen_examples_table_header_row:
            self.seen_examples_table_header_row = True
            return
        row_name = "%s (%s)" % (self.scenario, columns[1].strip())
        all_scenarios.append(Scenario(row_name, self.feature, location,
                                      self.tags | self.example_tags))


def process_feature_file(dir_path, file_name):
    dir_list = dir_path.split(os.sep)
    if dir_list[0] == os.curdir:
        dir_list = dir_list[1:]
    if dir_list[0].lower() == 'features':
        dir_list = dir_list[1:]
    if len(dir_list) > DIRECTORY_DEPTH_MAX:
        error("Too many nested directories for feature file: {} -> {}".format(
              file_name, dir_path), None)
    feature_tags = set()
    tags = set()
    in_examples = False
    scenario_outline = None
    feature_name = None
    with open(os.path.join(dir_path, file_name), 'r') as feature_file:
        for line_no, line in enumerate(feature_file, 1):
            here = Location(dir_list, file_name, line_no)
            line = line.strip()
            if in_examples:
                if line.startswith('|'):
                    columns = line.split('|')
                    scenario_outline.add_example(columns, here)
                    continue
                if not line.split('#', 1)[0].strip():
                    # Blank lines do not end an example table.
                    continue
                in_examples = False
                # deliberately fall through as there is no trailing/end marker
                # for an examples table.
                # do not end the scenario outline as there can be multiple
                # examples tables.
            if line.startswith('@'):
                tags |= tags_from(line, here)
            elif line.lower().startswith('feature:'):
                feature_name = summary_from(line)
                feature_tags = tags
                tags = set()
            elif line.lower().startswith('scenario:'):
                if feature_name is None:
                    error("Scenario occurred before/without Feature", here)
                all_scenarios.append(Scenario(summary_from(line),
                                              feature_name, here,
                                              tags | feature_tags))
                scenario_outline = None
                tags = set()
            elif line.lower().startswith('scenario outline:'):
                if feature_name is None:
                    error("Scenario Outline occurred before/without Feature",
                          here)
                scenario_outline = ScenarioOutline(summary_from(line),
                                                   feature_name, here,
                                                   tags | feature_tags)
                tags = set()
            elif line.lower().startswith('examples:'):
                if scenario_outline is None:
                    error("Examples outside of a Scenario Outline", here)
                    continue
                scenario_outline.new_example_table(tags)
                in_examples = True
                tags = set()


def is_feature_file(file_name):
    return file_name.lower().endswith('.feature')

for dir_path, dir_names, file_names in os.walk(os.curdir):
    if '.git' in dir_names:
        dir_names.remove('.git')
    if 'unUsedCode' in dir_names:
        dir_names.remove('unUsedCode')
    for file_name in filter(is_feature_file, file_names):
        process_feature_file(dir_path, file_name)

print_error_log()

if args.report:
    write_csv_row(csv_header_list)
    for scenario in sorted(all_scenarios, key=Scenario.sort_key):
        scenario.print_stats()

if error_log:
    sys.exit(ERROR_EXIT_CODE)
