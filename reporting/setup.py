import os
import setuptools
from shutil import rmtree
import subprocess
import sys

NAME = 'qe_coverage'
DESCRIPTION = 'Collection of tools to enable coverage reporting'
VERSION = None

CONSOLE_SCRIPTS = [
    'coverage-gherkin=qe_coverage.gherkin:main [gherkin]',
    'coverage-send-opencafe-report=qe_coverage.send_opencafe_tags_report:main',
    'coverage-cloned-repo=qe_coverage.coverage_cloned_repo:main',
    'coverage-opencafe=qe_coverage.collect_opencafe_coverage:main',
    'coverage-testlink=qe_coverage.send_testlink_tags_report:main',
    'coverage-history=qe_coverage.coverage_historical_repo:main',
]

INSTALL_REQUIRES = [
    'attrs>=16.0.0',
    'requests>=2.10',
    'tableread>=1.0.2',
    'qecommon_tools>=1.1.0',
    'wrapt',
    'python-dateutil',
]

EXTRAS_REQUIRE = {'gherkin': ['behave==1.2.6.dev1']}

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
                 author='Rackspace QE',
                 author_email='qe-tools-contributors@rackspace.com',
                 license='MIT',
                 entry_points={
                     'console_scripts': CONSOLE_SCRIPTS,
                 },
                 install_requires=INSTALL_REQUIRES,
                 packages=setuptools.find_packages(),
                 include_package_data=True,
                 zip_safe=False,
                 extras_require=EXTRAS_REQUIRE,
                 )
