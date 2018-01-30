import setuptools


setuptools.setup(
    name='qe_jira',
    version='1.0.0',
    description='Simple helper to create a QE Test JIRA from a dev JIRA',
    author='RBA QE',
    author_email='rba-qe@rackspace.com',
    license='MIT',
    packages=setuptools.find_packages(),
    install_requires=[
        'Click',
        'jira'
    ],
    entry_points={
        'console_scripts': ['qe_jira=qe_jira:test_jira_from']
    },
    include_package_data=True,
    zip_safe=False
)
