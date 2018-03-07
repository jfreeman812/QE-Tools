import setuptools


setuptools.setup(name='qecommon_tools',
                 version='1.1.0',
                 description='Collection of miscellaneous helper methods',
                 url='https://github.rackspace.com/QualityEngineering/QE-Tools',
                 author='RBA QE',
                 author_email='rba-qe@rackspace.com',
                 license='MIT',
                 packages=setuptools.find_packages(),
                 install_requires=[
                     'requests>=2.10'
                 ],
                 tests_require=['pytest'],
                 include_package_data=True,
                 zip_safe=False)
