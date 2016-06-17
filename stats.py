#!/usr/bin/env python

import csv
import os
import sys

from test_tags import TestTags

write_csv_row = csv.writer(sys.stdout).writerow

# NOTE: This is not (yet) a general Gherkin file validator/checker,
#       so weirdly formatted Gherkin might slip through.

tag_file_name = 'tags.md'
try:
    script_name, tag_file_name = sys.argv
except:
    pass

tags = TestTags(tag_file_name)

# Hard coded until I add to tags.md?
group_default = {
    'polarity': "TBD",
    'environment': "ALL",
    'priority': "p1",
    'status': "Operational",
    'suite': "ALL"
}

master_tags = set(tags.keys())

group_list = sorted(tags.groups.keys())
csv_header_list = group_list + ['feature file', 'feature hierarchy...']


def tags_from(line):
    # we don't have to check for leading '@',
    # those will automatically fail the master tags check
    tags = set(line.split())
    bad_tags = tags - master_tags
    if bad_tags:
        print "Unsupported tags:", ",".join(bad_tags)
    return tags


def one_tag_from(have_tags, tag_set, default_value):
    targets = have_tags & tag_set
    if len(targets) > 1:
        print "Mutually exclusive tags:", " ".join(targets)
    if not targets:
        return default_value
    tag = targets.pop()
    return tags.report_names.get(tag, "UNKNOWN TAG: %s" % (tag,))


all_scenarios = []


class Scenario(object):
    def __init__(self, scenario, line_no, file_name, dir_list, tags):
        self.scenario = scenario
        self.line_no = line_no
        self.file_name = file_name
        self.dir_list = dir_list
        self.tags = tags
        self.group = dict()
        self.analyze_tags()
        all_scenarios.append(self)

    @staticmethod
    def sort_key(obj):
        # using line_no will keep the sort stable if the scenario line changes.
        return (obj.dir_list, obj.file_name, obj.line_no)

    def analyze_tags(self):
        for group, tag_list in tags.groups.items():
            self.group[group] = one_tag_from(self.tags, tag_list,
                                             group_default[group])

    def print_stats(self):
        write_csv_row([self.group[x] for x in group_list] +
                      [self.file_name] + self.dir_list)


def process_feature_file(dir_path, file_name):
    dir_list = dir_path.split(os.sep)
    if dir_list[0] == os.curdir:
        dir_list = dir_list[1:]
    feature_tags = set()
    tags = set()
    with open(os.path.join(dir_path, file_name), 'r') as feature_file:
        for line_no, line in enumerate(feature_file, 1):
            line = line.strip()
            if line.startswith('@'):
                tags |= tags_from(line)
            elif line.lower().startswith('feature:'):
                feature_tags = tags
                tags = set()
            elif line.lower().startswith(('scenario:', 'scenario outline:')):
                scenario = line.split(':', 1)[1].strip()
                Scenario(scenario, line_no, file_name, dir_list,
                         tags | feature_tags)
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

write_csv_row(csv_header_list)

for scenario in sorted(all_scenarios, key=Scenario.sort_key):
    scenario.print_stats()
