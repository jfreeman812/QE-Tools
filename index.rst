QE-Tools
########

A collection of tools designed for use in the larger Rackspace QE Organization.


Coverage Metrics
----------------

The coverage metrics is a tagging standard adopted by a number of QE teams within Rackspace that can then be collected and aggregated for reporting.
The below document provides the necessary information for following this standard.

.. toctree::
   :maxdepth: 2

   Coverage Metrics <reporting/qe_coverage/coverage>


Libraries
---------

Several libraries have been created that can be installed via Artifactory_.

.. note::

    Example install usage:

    .. code-block:: bash

        $ pip install -i "https://artifacts.rackspace.net/artifactory/api/pypi/pypi/simple" <LIBRARY_NAME>


.. toctree::
   :hidden:

   qe_jira/README
   reporting/README
   sphinx-gherkindoc/README
   tableread/README

==================================================  ==============================================================================
Library Name                                        Description
==================================================  ==============================================================================
:doc:`qe_jira<qe_jira/README>`                      Quickly creates a JIRA on a QE board for testing of a JIRA from a dev board
qecommon_tools                                      A library for helper functions across QE-Tools designed for larger consumption
:doc:`qe_coverage<reporting/README>`                A collection of tools for QE-related reporting
:doc:`sphinx-gherkindoc<sphinx-gherkindoc/README>`  A tool to convert Gherkin into Sphinx documentation
:doc:`tableread<tableread/README>`                  A library for converting reStructredText tables into Python objects
==================================================  ==============================================================================

Local Scripts
-------------

In addition to libraries that can be installed via `pip`, this repository provides several scripts that can be utilized for various needs.

.. toctree::
   :hidden:

   etcd/README
   git-support/README
   httpbin-data/README

===================================================  ==================================================================================
File Name                                            Description
===================================================  ==================================================================================
check-unicode.py                                     Checks a directory structure for Unicode errors in Python, Ruby, and Feature files
pr-checker.py                                        Checks a GitHub organization for PRs that have not been updated in a given time
:doc:`etcd/<etcd/README>`                            A collection of tools for using etcd
:doc:`git-support/<git-support/README>`              Helpful git hooks
:doc:`httpbin-data/<httpbin-data/README>`            An enhancement to httpbin that provides data-persistent endpoints
`splunk_forwarder/`_                                   Web app that collects data from `qe_coverage` and forwards it to Splunk
===================================================  ==================================================================================

.. _Artifactory: https://artifacts.rackspace.net
.. _`splunk_forwarder/`: https://qetools.rax.io/splunk/doc/
