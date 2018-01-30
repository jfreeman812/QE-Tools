import setuptools


setuptools.setup(name='qe_coverage',
                 version='1.0.8',
                 description='Collection of tools to enable coverage reporting',
                 url='https://github.rackspace.com/QualityEngineering/QE-Tools',
                 author='RBA QE',
                 author_email='rba-qe@rackspace.com',
                 license='MIT',
                 entry_points={
                     'console_scripts': [
                        'coverage-gherkin=qe_coverage.gherkin:main [gherkin]',
                        'coverage-send-opencafe-report=qe_coverage.send_opencafe_tags_report:main',
                        'coverage-cloned-repo=qe_coverage.coverage_cloned_repo:main',
                        'coverage-opencafe=qe_coverage.collect_opencafe_coverage:main',
                     ],
                 },
                 packages=setuptools.find_packages(),
                 install_requires=['attrs==17.3.0', 'requests>=2.10', 'tableread>=1.0.2',
                                   'qecommon_tools>=1.0.1', 'wrapt'],
                 extras_require={'gherkin': ['behave==1.2.6.dev1']},
                 include_package_data=True,
                 zip_safe=False)
