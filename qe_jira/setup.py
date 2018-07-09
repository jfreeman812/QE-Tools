import os
import setuptools

NAME = 'qe_jira'
DESCRIPTION = 'Simple helpers to interface to JIRA from an API or command line.'
VERSION = None

CONSOLE_SCRIPTS = [
    'qe_jira=qe_jira:_create_qe_jira_from',
    'jira-make-linked-issue=qe_jira:_create_qe_jira_from',
    'jira-add-comment=qe_jira:_cli_add_comment',
    'jira-example-config=qe_jira:_example_config_install',
]

INSTALL_REQUIRES = [
    'jira',
    'qecommon_tools>=1.0.2',
    'configparser ; python_version<"3.5"',  # backport required for py2 compatibility
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
