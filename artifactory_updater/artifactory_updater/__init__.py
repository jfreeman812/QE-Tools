import json
import os
from pkg_resources import parse_version
import setuptools
from shutil import rmtree
import subprocess
import sys
try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen


class ArtifactoryCommand(setuptools.Command):
    '''Support setup.py Artifactory Distribution'''

    description = 'Build and publish the package to Artifactory'
    artifactory_domain = 'artifacts.rackspace.net'
    user_options = [('dry-run', None, 'Check without updating')]
    here = None
    package_name = None
    package_version = None

    def initialize_options(self):
        self.dry_run = None

    def finalize_options(self):
        self.dry_run = True if self.dry_run is not None else False

    def _validate_package_setup(self):
        pypirc_path = os.path.join(os.path.expanduser('~'), '.pypirc')
        with open(pypirc_path, 'r') as f:
            if not any((self.package_name in x for x in f)):
                message = 'Package {} does not have a config section in {}'
                raise KeyError(message.format(self.package_name, pypirc_path))

    def _latest_artifactory_version(self):
        package_url = 'https://{0}/artifactory/api/storage/{1}-pypi-local/{1}'
        response = urlopen(package_url.format(self.artifactory_domain, self.package_name))
        package_data = json.loads(response.read())
        versions = [x['uri'].lstrip('/') for x in package_data['children']]
        return max(versions, key=parse_version)

    def _package_out_of_date(self):
        artifactory_version = self._latest_artifactory_version()
        if parse_version(self.package_version) <= parse_version(artifactory_version):
            return ''
        message = 'Current Version: {}; Latest Artifactory Version: {}'
        return message.format(self.package_version, artifactory_version)

    def run(self):
        self._validate_package_setup()
        out_of_date_msg = self._package_out_of_date()
        if not out_of_date_msg:
            print('{} is up to date!'.format(self.package_name))
            sys.exit()
        print('{} needs to be updated: {}'.format(self.package_name, out_of_date_msg))
        if self.dry_run:
            sys.exit()
        print('Removing previous builds...')
        rmtree(os.path.join(self.here, 'dist'), ignore_errors=True)
        rmtree(os.path.join(self.here, 'build'), ignore_errors=True)
        print('Building and uploading sdist...')
        sdist_command = '{} setup.py sdist upload -r {{}}'.format(sys.executable)
        subprocess.call(sdist_command.format(self.package_name).split(), cwd=self.here)
        print('Building and uploading wheel...')
        bdist_command = '{} setup.py bdist_wheel --universal upload -r {{}}'.format(sys.executable)
        subprocess.call(bdist_command.format(self.package_name).split(), cwd=self.here)
        sys.exit()
