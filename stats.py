#!/usr/bin/env python
import os
from collections import Counter

# NOTE: This should use the csv module to write the output.
# NOTE: This is not a general Gherkin file validator/checker,
#       so weirdly formatted Gherkin might slip through.

# Get this list from Ben's new module to be, hard-coding for the moment.
master_tags_list = [
    '@nyi',
    '@needs-work',
    '@bvt',
    '@smoke',
    '@load',
    '@destructive',
    '@solo',
    '@production-only',
    '@staging-only',
    '@mvp',
    '@positive',
    '@negative']
master_tags_set = set(master_tags_list)

scenario_count = 'scenario count'
master_count_list = [scenario_count] + master_tags_list
header_list = master_count_list + ['feature file', 'directory path...']


def tags_from(line):
    """Note that we don't have to check for leading '@' since those
       will automatically fail the master tags check"""
    parts = set(line.split())
    bad_parts = parts - master_tags_set
    if bad_parts:
        print "Unsupported tags:", ",".join(bad_parts)
    return parts & master_tags_set


def processFeatureFile(dirpath, filename):
    dirlist = dirpath.split(os.sep)
    if dirlist[0] == os.curdir:
        dirlist = dirlist[1:]
    myCounter = Counter()
    feature_tags = set()
    tags = set()
    with open(os.path.join(dirpath, filename), 'r') as feature_file:
        for line in feature_file:
            line = line.strip()
            if line.startswith('@'):
                tags |= tags_from(line)
            elif line.lower().startswith('feature:'):
                feature_tags = tags
                tags = set()
            elif line.lower().startswith(('scenario:', 'scenario outline:')):
                myCounter[scenario_count] += 1
                myCounter.update(tags)
                myCounter.update(feature_tags)
                tags = set()
    counts = map(lambda k: "%3d" % myCounter.get(k, 0), master_count_list)
    print ",".join(counts + [filename] + dirlist)


def is_feature_file(filename):
    return filename.lower().endswith('.feature')

print ",".join(header_list)
for dirpath, dirnames, filenames in os.walk(os.curdir):
    if '.git' in dirnames:
        dirnames.remove('.git')
    if 'unUsedCode' in dirnames:
        dirnames.remove('unUsedCode')
    for filename in filter(is_feature_file, filenames):
        processFeatureFile(dirpath, filename)
