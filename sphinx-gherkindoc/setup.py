import setuptools


setuptools.setup(name='sphinx_gherkindoc',
                 version='1.0.0',
                 description='An tool to convert Gherkin files into Sphinx documentation',
                 url='https://github.rackspace.com/QualityEngineering/QE-Tools',
                 author='RBA QE',
                 author_email='rba-qe@rackspace.com',
                 license='MIT',
                 entry_points={
                     'console_scripts': ['sphinx-gherkindoc=sphinx_gherkindoc:main'],
                 },
                 packages=setuptools.find_packages(),
                 # Until the behave project accepts our PR or otherwise fixes the bug in
                 # model_core.py, the behave version must be pinned.
                 install_requires=['Sphinx>=1.3,<1.7', 'behave==1.2.6.dev1'],
                 include_package_data=True,
                 zip_safe=False)
