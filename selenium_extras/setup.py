# Copyright 2016, 2018 Rackspace
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os
import setuptools

NAME = 'selenium_extras'
DESCRIPTION = 'Selenium Extra Classes for Great Good'
VERSION = None

CONSOLE_SCRIPTS = [
]

INSTALL_REQUIRES = [
    'selenium~=3.12.0',
]

TESTS_REQUIRE = [
]

EXTRAS_REQUIRE = {}

here = os.path.abspath(os.path.dirname(__file__))

about = {}
if not VERSION:
    with open(os.path.join(here, NAME, '__version__.py')) as f:
        exec(f.read(), about)
else:
    about['__version__'] = VERSION


setuptools.setup(name=NAME,
                 version=about['__version__'],
                 description=DESCRIPTION,
                 url='https://github.rackspace.com/QualityEngineering/QE-Tools',
                 author='Rackspace Cloud QE, Rackspace QE',
                 author_email='qe-tools-contributors@rackspace.com',
                 license='Apache License, Version 2.0',
                 entry_points={
                     'console_scripts': CONSOLE_SCRIPTS,
                 },
                 install_requires=INSTALL_REQUIRES,
                 packages=setuptools.find_packages(),
                 tests_require=TESTS_REQUIRE,
                 include_package_data=True,
                 zip_safe=False,
                 extras_require=EXTRAS_REQUIRE,
                 )
