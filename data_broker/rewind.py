#! /usr/bin/env python

import argparse
import glob
import json
import lzma
import os
import sys
import time

import requests

from app import PROD_DATA_DIR

FILENAME_TIMESTAMP_FORMAT = '%Y%m%d_%H%M%S'
POST_URL = 'https://qetools.rax.io/coverage/production'


def main(file_paths=None):
    file_paths = file_paths or glob.glob('{}/*/*.xz'.format(PROD_DATA_DIR))
    for filename in file_paths:
        epoch_stamp = time.mktime(time.strptime(
            filename.split('/')[-1].rstrip('.xz'), FILENAME_TIMESTAMP_FORMAT
        ))
        with lzma.open(filename) as f:
            data = json.loads(f.read())
        response = requests.post(
            POST_URL, json=data, params={'timestamp': epoch_stamp, 'is_rewind': True}
        )
        if response.status_code != 201:
            print('Upload for "{}" failed!'.format(filename))


if __name__ == '__main__':
    parser = argparse.ArgumentParser('DataBroker Data Rewind')
    parser.add_argument('files', nargs='*', help='Paths to files to rewind through the broker')
    args = parser.parse_args()
    main(args.files)
