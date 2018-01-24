#!/usr/bin/env python

import argparse
import glob
import os
import shutil
import subprocess
import sys
from tempfile import mkdtemp

from qecommon_tools import cleanup_and_exit, safe_run

cloned_repo_dir_name = 'cloned_repo'

starting_directory = os.getcwd()


def main():
    parser = argparse.ArgumentParser(description='Generate Coverate Reports for a cloned repo')
    parser.add_argument('repo_to_clone',
                        help='the name of the repo to clone.'
                             ' In the format: <organization>/<repo-name>.'
                             ' Do not include the URL or the trailing ".git"')
    parser.add_argument('coverage_script',
                        help='The command to generate and publish coverage and its parameters.'
                             ' NOTE: coverage_script will be run from the top level directory'
                             ' of the cloned repo.')
    args, coverage_args = parser.parse_known_args()

    tmp_dir_name = mkdtemp()

    os.chdir(tmp_dir_name)

    clone_command = ['git',
                     'clone',
                     'git@github.rackspace.com:{}.git'.format(args.repo_to_clone),
                     cloned_repo_dir_name,
                     '--depth',
                     '1']

    safe_run(clone_command)

    os.chdir(cloned_repo_dir_name)

    safe_run([args.coverage_script] + coverage_args)

    os.chdir(starting_directory)
    cleanup_and_exit(dir_name=tmp_dir_name)


if __name__ == '__main__':
    main()
