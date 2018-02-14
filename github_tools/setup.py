import setuptools


setuptools.setup(name='github_tools',
                 version='1.0.1',
                 description='A collection of tools for interacting with GitHub',
                 url='https://github.rackspace.com/QualityEngineering/QE-Tools',
                 author='Rackspace QE',
                 author_email='rba-qe@rackspace.com',
                 license='MIT',
                 entry_points={
                     'console_scripts': [
                         'gt-pr-checker=github_tools:pr_checker',
                         'gt-install-hooks=github_tools:install_hooks',
                     ],
                 },
                 install_requires=['requests>=2.10', 'github3.py>=0.9', 'qecommon_tools>=1.0.3'],
                 packages=setuptools.find_packages(),
                 include_package_data=True,
                 zip_safe=False)
