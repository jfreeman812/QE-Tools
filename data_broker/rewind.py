#! /usr/bin/env python

import glob
import json
import os
import lzma
import sys
import time

import requests

FILENAME_TIMESTAMP_FORMAT = '%Y%m%d_%H%M%S'
USER_HOME = os.path.expanduser('~')
LOCAL_POST_URL = 'http://localhost:6969/coverage/production?timestamp={}&is_rewind=True'


def main(*file_paths):
    files = file_paths or glob.glob('{}/data_broker_files/*/*.xz'.format(USER_HOME))
    for filename in files:
        epoch_stamp = time.mktime(time.strptime(
            filename.split('/')[-1].rstrip('.xz'), FILENAME_TIMESTAMP_FORMAT
        ))
        with lzma.open(filename) as f:
            data = json.loads(f.read())
        response = requests.post(
            LOCAL_POST_URL.format(epoch_stamp), json=data
        )
        response.raise_for_status()


if __name__ == '__main__':
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    main(*args)
