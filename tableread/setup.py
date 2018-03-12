import os
import setuptools

from artifactory_updater import ArtifactoryCommand

NAME = 'tableread'
DESCRIPTION = 'Table reader for simple reStructredText tables'
VERSION = None

CONSOLE_SCRIPTS = [
]

INSTALL_REQUIRES = [
    'attrs>=16.0.0'
]

EXTRAS_REQUIRE = {}

here = os.path.abspath(os.path.dirname(__file__))

about = {}
if not VERSION:
    with open(os.path.join(here, NAME, '__version__.py')) as f:
        exec(f.read(), about)
else:
    about['__version__'] = VERSION


class TablereadArtifactory(ArtifactoryCommand):
    here = here
    package_name = NAME
    package_version = about['__version__']


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
                 cmdclass={
                     'artifactory': TablereadArtifactory
                 })
