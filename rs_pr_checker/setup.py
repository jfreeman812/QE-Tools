import setuptools


setuptools.setup(name='pr_checker',
                 version='1.0.0',
                 description='A tool that will notifiy assignees for overdue PRs',
                 url='https://github.rackspace.com/QualityEngineering/QE-Tools',
                 author='Rackspace QE',
                 author_email='rba-qe@rackspace.com',
                 license='MIT',
                 entry_points={'console_scripts': ['rs-pr-checker=rs_pr_checker:cli']},
                 install_requires=['requests>=2.10', 'github3.py>=0.9'],
                 packages=setuptools.find_packages(),
                 include_package_data=True,
                 zip_safe=False)
