#! /usr/bin/env python

import argparse
import glob
import json
import lzma

from prod_data_dir import PROD_DATA_DIR


def main(key, from_value, to_value, file_paths=None):
    for filename in file_paths or glob.glob('{}/*/*.xz'.format(PROD_DATA_DIR)):
        needs_write = False
        with lzma.open(filename) as f:
            data = json.loads(f.read())
        for entry in data:
            if entry.get(key) == from_value:
                entry[key] = to_value
                needs_write = True
        if needs_write:
            with lzma.open(filename, 'wt') as f:
                f.write(json.dumps(data))


if __name__ == '__main__':
    parser = argparse.ArgumentParser('DataBroker Data Rename')
    parser.add_argument('key', help='The entry key value to check and rename.')
    parser.add_argument('from_value', help='The current string value to be renamed')
    parser.add_argument('to_value', help='The new string value to be written')
    help_msg = ('Paths to files to read for renaming. '
                'By default, all files in {} will be read.'.format(PROD_DATA_DIR))
    parser.add_argument('-f', '--file', dest='files', action='append', help=help_msg)
    args = parser.parse_args()
    main(args.key, args.from_value, args.to_value, args.files)

