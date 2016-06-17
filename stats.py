#!/usr/bin/env python

import csv
import os
import sys

write_csv_row = csv.writer(sys.stdout).writerow

# NOTE: This is not (yet) a general Gherkin file validator/checker,
#       so weirdly formatted Gherkin might slip through.

############
# This section to the marker below is temporary until we get Ben's new
# tags parser merged.
#

tag_mappings = dict()

suite_tags = set([
    '@bvt',
    '@smoke',
    '@load',
    '@destructive',
    '@solo'])
for tag in suite_tags:
    tag_mappings[tag] = tag[1:]

status_tags = set([
    '@nyi',
    '@needs-work'])
tag_mappings['@nyi'] = 'NYI'
tag_mappings['@needs-work'] = 'Needs Work'

priority_tags = set([
    '@mvp'])
tag_mappings['@mvp'] = "p0"

environment_tags = set([
    '@production-only',
    '@staging-only'])
tag_mappings['@production-only'] = "Production"
tag_mappings['@staging-only'] = "Staging"

polarity_tags = set([
    '@positive',
    '@negative'])
tag_mappings['@positive'] = 'P'
tag_mappings['@negative'] = 'N'

master_tags_set = (status_tags | suite_tags | priority_tags |
                   environment_tags | polarity_tags)

#
############


csv_header_list = ['suite', 'status', 'priority', 'environment', 'polarity',
                   'scenario', 'feature file', 'feature hierarchy...']


def tags_from(line):
    """Note that we don't have to check for leading '@' since those
       will automatically fail the master tags check"""
    tags = set(line.split())
    bad_tags = tags - master_tags_set
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
    return tag_mappings.get(tag, "UNKNOWN TAG: %s" % (tag,))


all_scenarios = []


class Scenario(object):
    def __init__(self, scenario, line_no, file_name, dir_list, tags):
        self.scenario = scenario
        self.line_no = line_no
        self.file_name = file_name
        self.dir_list = dir_list
        self.tags = tags
        self.analyze_tags()
        all_scenarios.append(self)

    @staticmethod
    def sort_key(obj):
        return (obj.dir_list, obj.file_name, obj.line_no)

    def analyze_tags(self):
        self.polarity = one_tag_from(self.tags, polarity_tags, "TBD")
        self.environment = one_tag_from(self.tags, environment_tags, "ALL")
        self.priority = one_tag_from(self.tags, priority_tags, "p1")
        self.status = one_tag_from(self.tags, status_tags, "Operational")
        self.suite = one_tag_from(self.tags, suite_tags, "ALL")

    def print_stats(self):
        write_csv_row([self.suite, self.status, self.priority,
                       self.environment, self.polarity, self.scenario,
                       self.file_name] + self.dir_list)


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
