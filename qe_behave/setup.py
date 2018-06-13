import os
import setuptools

NAME = 'qe_behave'
DESCRIPTION = 'QE behave-based testing'
VERSION = None

CONSOLE_SCRIPTS = [
]

# NOTE: Compatibility checks for other QE-Tools packages are at the
# Major.Minor level; for third party packages, the patch level is included.
INSTALL_REQUIRES = [
    'qecommon_tools~=1.1',
    'qe_config~=1.0.0',
    'qe_logging~=1.1',
    'qe_coverage~=1.5',
    'sphinx_gherkindoc~=1.0',
    'behave~=1.2.6',
    'flake8~=3.5.0',
    'flake8-builtins~=1.4.1',
    'flake8-tuple~=0.2.13',
]

TESTS_REQUIRE = [
]

EXTRAS_REQUIRE = {
    'api': ['requests~=2.18.4'],
    'ui': ['selenium~=3.12.0',
           'selenium_extras~=0.1.0',
           ],
}


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
