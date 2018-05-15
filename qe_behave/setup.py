import os
import setuptools

NAME = 'qe_behave'
DESCRIPTION = 'QE behave-based testing'
VERSION = None

CONSOLE_SCRIPTS = [
]

INSTALL_REQUIRES = [
    'qecommon_tools>=1.1.7',
    'qe_logging>=1.1.1',
    'qe_coverage>=1.5.5',
    'sphinx_gherkindoc>=1.0.1',
    'behave>=1.2.6',
]

TESTS_REQUIRE = [
]

EXTRAS_REQUIRE = {
    'API': ['qe_requests'],   # Place holder!
    'GUI': ['selenium>=3.12'],
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
