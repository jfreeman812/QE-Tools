import os
import setuptools

NAME = 'qe_config'
DESCRIPTION = 'QE configuration tools'
VERSION = None

CONSOLE_SCRIPTS = [
]

# NOTE: Compatibility checks for other QE-Tools packages are at the
# Major.Minor level; for third party packages, the patch level is included.
INSTALL_REQUIRES = [
    'qecommon_tools~=1.1',
]

TESTS_REQUIRE = [
]

EXTRAS_REQUIRE = {
    'munch': ['munch~=2.3.2'],
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
