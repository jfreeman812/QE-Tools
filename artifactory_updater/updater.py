#! /usr/bin/env python

import argparse
from glob import glob
import os
import subprocess
import sys


PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def check_and_update(container_dir, update=True):
    print('Checking {}...'.format(container_dir))
    command = [
        sys.executable,
        '{}/setup.py'.format(container_dir),
        'artifactory'
    ]
    if not update:
        command.append('--dry-run')
    subprocess.call(command, cwd=PARENT_DIR)


def get_packages(dir_list=None):
    this_directory = os.path.split(os.path.dirname(os.path.abspath(__file__)))[-1]
    dir_list = dir_list or [x.split('/')[-2] for x in glob('../*/setup.py')]
    return filter(lambda x: x != this_directory, dir_list)


def main():
    parser = argparse.ArgumentParser()
    help_msg = 'Specific project directories to check. If none provided, all found are checked.'
    parser.add_argument('project_dir', nargs='*', help=help_msg)
    parser.add_argument('--dry-run', action='store_false', dest='update',
                        help='Check version data without uploading new versions when found.')
    args = parser.parse_args()
    for container_dir in get_packages(args.project_dir):
        check_and_update(container_dir, update=args.update)


if __name__ == '__main__':
    main()
