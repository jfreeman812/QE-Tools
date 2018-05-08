#! /usr/bin/env python

import argparse
import functools
import glob
import json
import lzma
import os
import sys
import time

import requests

from prod_data_dir import PROD_DATA_DIR

FILENAME_TIMESTAMP_FORMAT = '%Y%m%d_%H%M%S'
POST_URL = 'https://qetools.rax.io/coverage/production'


def _rename_entry(key, from_value, to_value, entry):
    if entry.get(key) == from_value:
        entry[key] = to_value


def _prep_rename_function(rename):
    key, from_value, to_value = rename.split(':')
    return functools.partial(_rename_entry, key, from_value, to_value)


def _rename_data(data, rename_funcs):
    for entry in data:
        for rename in rename_funcs:
            rename(entry)


def main(file_paths=None, renames=None):
    for filename in file_paths or glob.glob('{}/*/*.xz'.format(PROD_DATA_DIR)):
        epoch_stamp = time.mktime(time.strptime(
            filename.split('/')[-1].rstrip('.xz'), FILENAME_TIMESTAMP_FORMAT
        ))
        with lzma.open(filename) as f:
            data = json.loads(f.read())
        if renames:
            _rename_data(data, [_prep_rename_function(r) for r in renames])
        response = requests.post(
            POST_URL, json=data, params={'timestamp': epoch_stamp, 'is_rewind': True}
        )
        if response.status_code != 201:
            print('Upload for "{}" failed!'.format(filename))


if __name__ == '__main__':
    parser = argparse.ArgumentParser('DataBroker Data Rewind')
    help_msg = ('Paths to files to rewind through the broker. '
                'By default, all files in {} will be read.'.format(PROD_DATA_DIR))
    parser.add_argument('files', nargs='*', help=help_msg)
    rename_help = ('Keys to rename in the format <key>:<from_string>:<to_string>.'
                   '  Example: "Product Hierarchy:SPA:Scripted Parsing Analytics"')
    parser.add_argument('--rename', '-r', action='append', help=rename_help)
    args = parser.parse_args()
    main(args.files, args.rename)
