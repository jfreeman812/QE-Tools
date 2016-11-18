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
    print(__doc__)
    print()
    print('Usage: {} json-file-name'.format(sys.argv[0]))
    sys.exit(-1)


# Keep the newly created directory right next to the source JSON file,
# using the name of the JSON file sans-extension.
root_dir_name = os.path.splitext(json_file_name)[0]

# If the file has no extension, or if there is already a directory present,
# don't overwrite it, just bomb out and let the user handle it.
if os.path.exists(root_dir_name):
    print()
    print('File/Directory already exists: {}'.format(root_dir_name))
    sys.exit(-2)

file_blob = open(json_file_name).read()

try:
    file_json = json.loads(file_blob)
except:
    print('JSON decoding error in {}'.format(json_file_name))
    raise


def json_dump(obj, into):
    """Helper to encapsulate JSON output formatting which also
    squashes the Last Modification info for cleaner diffs.
    """

    obj.pop('LastModifiedBy', None)
    obj.pop('LastModifiedDate', None)
    json.dump(obj, into, indent=2, sort_keys=True)


def dump_list(list_obj, name_field, directory_name):
    dir_name = os.path.join(root_dir_name, directory_name)
    os.makedirs(dir_name)

    for member in list_obj:
        name = member[name_field]
        with open(os.path.join(dir_name, name), 'w') as member_file:
            json_dump(member, member_file)

dump_list(file_json['Process']['Members'], 'Name', 'Process')
dump_list(file_json['APIGroups'], 'APIGroupName', 'APIGroups')
dump_list(file_json['Actions'], 'Name', 'Actions')
dump_list(file_json['APIs'], 'APIName', 'APIs')
