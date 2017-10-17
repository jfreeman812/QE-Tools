#!/usr/bin/env python
"""
Scan the current directory tree for Gherkin feature files and check their
use of tags against the given tags file. Tags are used to generate a test
coverage report as well.

NOTES: The --interface command line switch is because we anticipate that
       all tests in one place are of one type. If we find a case where
       API and UI tests are in the same tree we will have to revisit this.
"""

import argparse
import csv
import json
import os
import sys

from collections import namedtuple, defaultdict

from test_tags import TestTags

DIRECTORY_DEPTH_MAX = 3  # As per JIRA QGTM-443, which has to be manually tracked for now.
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


error_log = []


def error(msg, location):
    error_log.append((msg, location))


def print_error_log_csv():
    if not error_log:
        return
    # For error reporting we decided not to label the individual
    # path columns (unlike for the main report).
    write_csv_row(['Error', 'File', 'Line No', 'Path'])
    for (msg, location) in error_log:
        row = [msg]
        if location is not None:
            row.append(location.file_name)
            row.append(location.line_no)
            row.extend(location.dir_list)
        write_csv_row(row)


def print_error_log_one_line():
    for (msg, location) in error_log:
        if location is not None:
            msg += ", at: {}".format(location)
        print(msg)


def print_error_log_grep():
    for (msg, location) in error_log:
        if location is not None:
            msg = "{}:{}:{}".format(location.full_path(), location.line_no,
                                    msg)
        print(msg)


error_reporter_prefix = "print_error_log_"


def is_error_reporter_name(x):
    return x.startswith(error_reporter_prefix)


def short_error_name(x):
    return x.split(error_reporter_prefix, 1)[1]


error_reporters = [short_error_name(x) for x in globals() if is_error_reporter_name(x)]

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--legacy', default=False, action='store_true',
                    help='permit unknown tags without complaining. For legacy repos ONLY!')
parser.add_argument('-r', '--report', default=False, action='store_true',
                    help='generate/print a CSV coverage report')
# Adding in JSON as a new option for now as QGTM-444 is still in progress.
# When QGTM-444 closes, we will have pull to publish the JSON not CSV and the '-r' report
# will then be the JSON report.
parser.add_argument('--json', default=False, action='store_true',
                    help='generate/print a JSON coverage report')
parser.add_argument('-t', '--tagsfile', type=str, default=tags_file_name, metavar='FILE',
                    help="Specify a different tags file to consult")
parser.add_argument('-e', type=str, default='one_line', choices=error_reporters,
                    help="which format for error logging")
parser.add_argument('-i', '--interface', type=str, default='api', choices=('api', 'ui'),
                    help="which kind of tests are in this report")

args = parser.parse_args()

tags = TestTags(args.tagsfile)

master_tags = set(tags.keys())

group_list = sorted(tags.report_groups())


class Location(namedtuple('Location', ['dir_list', 'file_name', 'line_no'])):
    def full_path(self):
        return os.path.join(*(self.dir_list + [self.file_name]))

    def __str__(self):
        return "%s, line: %s" % (self.full_path(), self.line_no)


_allow_unknown_tags = set('@quarantined @nyi @needs-work'.split())


def tags_from(line, location):
    # we don't have to check for leading '@',
    # those will automatically fail the master tags check
    line = line.split('#', 1)[0]
    tags = set(line.split())
    bad_tags = tags - master_tags
    if (not args.legacy) and bad_tags and (not _allow_unknown_tags & tags):
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


class Scenario:
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

    def stats(self):
        stat_json = {group_name: self.group[group_name]
                     for group_name in group_list}
        # By convention, we take the top level directory to be the product name
        stat_json['product'] = self.location.dir_list[0]
        stat_json['project'] = 'n/a'
        stat_json['test name'] = self.scenario
        stat_json['interface type'] = args.interface
        stat_json['feature'] = self.feature
        stat_json['feature file'] = self.location.file_name
        # Since top level directory is captured in product above, skip it here.
        stat_json['categories'] = self.location.dir_list[1:]
        return stat_json


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
    if dir_list and dir_list[0].lower() == 'features':
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

print_error_log = globals().get(error_reporter_prefix + args.e,
                                print_error_log_one_line)

print_error_log()

all_stats = [scenario.stats() for scenario in sorted(all_scenarios, key=Scenario.sort_key)]

if args.report:
    fixed_fields = group_list + ['product', 'project', 'interface type', 'test name',
                                 'feature', 'feature file']
    category_headers = ['level %d' % (x + 1) for x in range(DIRECTORY_DEPTH_MAX)]

    write_csv_row(fixed_fields + category_headers)
    for stat in all_stats:
        write_csv_row([stat[x] for x in fixed_fields] + stat['categories'])

if args.json:
    json.dump(all_stats, sys.stdout, indent=2, sort_keys=True)
    print()

if error_log:
    sys.exit(ERROR_EXIT_CODE)