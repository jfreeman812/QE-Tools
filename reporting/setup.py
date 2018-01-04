import setuptools


setuptools.setup(name='qe_coverage',
                 version='1.0.1',
                 description='Collection of tools to enable coverage reporting',
                 url='https://github.rackspace.com/QualityEngineering/QE-Tools',
                 author='RBA QE',
                 author_email='rba-qe@rackspace.com',
                 license='MIT',
                 entry_points={
                     'console_scripts': ['coverage-gherkin=qe_coverage.gherkin:main [gherkin]'],
                 },
                 scripts=['coverage-cloned-repo.sh'],
                 packages=setuptools.find_packages(),
                 install_requires=['attrs==17.3.0', 'requests==2.18.4', 'tableread==1.0.2',
                                   'qecommon_tools>=1.0.0'],
                 extras_require={'gherkin': ['behave==1.2.6.dev1']},
                 include_package_data=True,
                 zip_safe=False)
