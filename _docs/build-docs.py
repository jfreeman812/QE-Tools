#! /usr/bin/env python
import argparse
import os
import subprocess
import sys


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    # Setup environment variables
    commit_id = str(subprocess.check_output(['git', 'rev-parse', 'HEAD'])).rstrip('\n')
    os.environ['GIT_COMMIT_ID'] = commit_id
    origin_url = str(subprocess.check_output(['git', 'config', '--get', 'remote.origin.url']))
    os.environ['GIT_ORIGIN_URL'] = origin_url.rstrip('\n')
    # Build parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--setup', action='store_true', help='Install needed libraries')
    args = parser.parse_args()
    # Run necessary commands
    if args.setup:
        try:
            pip_install = ['pip', 'install', '-r', '{}/requirements.txt'.format(BASE_DIR)]
            subprocess.check_call(pip_install)
        except BaseException:
            print('Environment setup failed; aborting self-checks')
            sys.exit(1)
    subprocess.call(['sphinx-apidoc', '--output-dir', 'docs', '--no-toc', '--force',
                     'qecommon_tools/qecommon_tools'])
    subprocess.call(['sphinx-build', '-c', BASE_DIR, '-aE', '.', 'docs/'])


if __name__ == '__main__':
    main()
