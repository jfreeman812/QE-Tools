#! /usr/bin/env python
import argparse
import distutils
import os
import shutil
import subprocess
import sys

from qecommon_tools import must_be_in_virtual_environment


DOCS_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(DOCS_DIR)


def main():
    # Setup environment variables
    commit_id = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=BASE_DIR,
                                        universal_newlines=True)
    os.environ['GIT_COMMIT_ID'] = commit_id.rstrip('\n')
    origin_url = subprocess.check_output(['git', 'config', '--get', 'remote.origin.url'],
                                         cwd=BASE_DIR, universal_newlines=True)
    os.environ['GIT_ORIGIN_URL'] = origin_url.rstrip('\n')
    # Build parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--setup', action='store_true', help='Install needed libraries')
    parser.add_argument('--clean', action='store_true',
                        help='Delete the output directory before starting to build documents')
    args = parser.parse_args()

    if distutils.spawn.find_executable('dot') is None:
        print("Cannot find 'dot', the graphviz utility we use to draw class inheritance diagrams.")
        print('Please install graphviz and try again.')
        sys.exit(1)

    # Run necessary commands
    if args.clean:
        shutil.rmtree('docs', ignore_errors=True)
    if args.setup:
        must_be_in_virtual_environment()
        try:
            pip_install = ['pip', 'install', '-r', '{}/requirements.txt'.format(DOCS_DIR)]
            subprocess.check_call(pip_install, cwd=BASE_DIR)
        except BaseException:
            print('Environment setup failed; aborting self-checks')
            sys.exit(1)
    sphinx_apidoc_cmd = ['sphinx-apidoc', '--output-dir', 'docs', '--no-toc',
                         '--force', '--module-first']
    subprocess.call(sphinx_apidoc_cmd + ['qecommon_tools/qecommon_tools'], cwd=BASE_DIR)
    subprocess.call(sphinx_apidoc_cmd + ['qe_logging/qe_logging'], cwd=BASE_DIR)
    subprocess.call(sphinx_apidoc_cmd + ['qe_config/qe_config'], cwd=BASE_DIR)
    subprocess.call(sphinx_apidoc_cmd + ['selenium_extras/selenium_extras'], cwd=BASE_DIR)
    subprocess.call(sphinx_apidoc_cmd + ['qe_jira/qe_jira'], cwd=BASE_DIR)
    subprocess.check_call(['sphinx-build', '-c', DOCS_DIR, '-aEW', '.', 'docs/'], cwd=BASE_DIR)


if __name__ == '__main__':
    main()
