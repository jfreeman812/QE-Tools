import setuptools


setuptools.setup(
    name='qe_jira',
    version='1.0.5',
    description='Simple helper to create a QE Test JIRA from a dev JIRA',
    author='QE Tools Contributors',
    author_email='qe-tools-contributors@rackspace.com',
    license='MIT',
    packages=setuptools.find_packages(),
    install_requires=[
        'pbr',  # jira library has a bug where it does not install this one library
        'jira',
        'qecommon_tools>=1.0.2',
        'configparser ; python_version<"3.5"',  # backport required for py2 compatibility
    ],
    entry_points={
        'console_scripts': ['qe_jira=qe_jira:create_qe_jira_from']
    },
    include_package_data=True,
    zip_safe=False
)
