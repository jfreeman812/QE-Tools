#!/usr/bin/env python
"""
Scan the given file ARICV V2.5 Process export JSON and break it into
separate files and pieces in the file system under a directory named
for the root name of the JSON file. (This tool does not attempt to validate
the intput JSON actually came from ARIC V2.5)
"""
import json
import os
import sys

try:
    _, json_file_name = sys.argv
except:
    print __doc__
    print
    print 'Usage: ', sys.argv[0], 'json-file-name'
    sys.exit(-1)


root_dir_name = os.path.splitext(json_file_name)[0]

if os.path.exists(root_dir_name):
    print
    print 'File/Directory already exists:', root_dir_name
    sys.exit(-2)

file_blob = open(json_file_name).read()

try:
    file_json = json.loads(file_blob)
except:
    print 'JSON decoding error in', json_file_name
    raise


# Common JSON formatting and squash LastModified info to make diff cleaner.
def json_dump(obj, into):
    obj.pop('LastModifiedBy', None)
    obj.pop('LastModifiedDate', None)
    json.dump(obj, into, indent=2, sort_keys=True)


def dumpList(list_obj, name_field, directory_name):
    dir_name = os.path.join(root_dir_name, directory_name)
    os.makedirs(dir_name)

    for member in list_obj:
        name = member[name_field]
        with open(os.path.join(dir_name, name), 'w') as member_file:
            json_dump(member, member_file)

dumpList(file_json['Process']['Members'], 'Name', 'Process')
dumpList(file_json['APIGroups'], 'APIGroupName', 'APIGroups')
dumpList(file_json['Actions'], 'Name', 'Actions')
dumpList(file_json['APIs'], 'APIName', 'APIs')
