#! /usr/bin/env python

import argparse
from glob import glob
import json
import os
from pkg_resources import parse_version
from shutil import rmtree
import subprocess
import sys
try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen


ARTIFACTORY_DOMAIN = 'artifacts.rackspace.net'
PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def _get_setup_info(container_dir, flag):
    return subprocess.check_output([
        sys.executable,
        '{}/setup.py'.format(container_dir),
        '--{}'.format(flag)
    ], universal_newlines=True, cwd=PARENT_DIR).strip('\n')


def _latest_artifactory_version(package_name):
    package_url = 'https://{0}/artifactory/api/storage/{1}-pypi-local/{1}'
    response = urlopen(package_url.format(ARTIFACTORY_DOMAIN, package_name)).read()
    if isinstance(response, bytes):
        response = response.decode('utf-8')
    package_data = json.loads(response)
    versions = [x['uri'].lstrip('/') for x in package_data['children']]
    return max(versions, key=parse_version)


def _update(container_dir, pkg_name):
    dist_path = os.path.join(PARENT_DIR, container_dir)
    print('Removing previous builds...')
    rmtree(os.path.join(dist_path, 'dist'), ignore_errors=True)
    rmtree(os.path.join(dist_path, 'build'), ignore_errors=True)
    print('Building and uploading sdist...')
    sdist_command = '{} setup.py sdist upload -r {{}}'.format(sys.executable)
    subprocess.call(sdist_command.format(pkg_name).split(), cwd=dist_path)
    print('Building and uploading wheel...')
    bdist_command = '{} setup.py bdist_wheel --universal upload -r {{}}'.format(sys.executable)
    subprocess.call(bdist_command.format(pkg_name).split(), cwd=dist_path)


def check_and_update(container_dir, update=True):
    pkg_name = _get_setup_info(container_dir, 'name')
    print('Checking {}...'.format(pkg_name))
    pkg_version = _get_setup_info(container_dir, 'version')
    artifactory_version = _latest_artifactory_version(pkg_name)
    if parse_version(pkg_version) <= parse_version(artifactory_version):
        print('{} is up to date!'.format(pkg_name))
        return
    message = '{} needs to be updated: Current Version: {}; Latest Artifactory Version: {}'
    print(message.format(pkg_name, pkg_version, artifactory_version))
    if update:
        _update(container_dir, pkg_name)


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
