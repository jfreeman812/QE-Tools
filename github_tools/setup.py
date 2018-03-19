import os
import setuptools

NAME = 'github_tools'
DESCRIPTION = 'A collection of tools for interacting with GitHub'
VERSION = None

CONSOLE_SCRIPTS = [
    'gt-pr-checker=github_tools:pr_checker',
    'gt-install-hooks=github_tools:install_hooks',
]

INSTALL_REQUIRES = [
    'requests>=2.10',
    'github3.py>=0.9',
    'qecommon_tools>=1.0.3'
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
