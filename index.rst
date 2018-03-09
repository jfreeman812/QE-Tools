QE-Tools
========

A collection of tools designed for use in the larger Rackspace QE Organization.

Libraries
---------

Several libraries have been created that can be installed via :doc:`Artifactory<artifactory>`.

.. note::

    Example install usage:

    .. code-block:: bash

        $ pip install -i "https://artifacts.rackspace.net/artifactory/api/pypi/pypi/simple" <LIBRARY_NAME>


.. toctree::
   :hidden:
   :caption: Libraries

   qe_jira <qe_jira/README>
   qecommon_tools <docs/qecommon_tools>
   qe_coverage <reporting/qe_coverage>
   github_tools <github_tools/README>
   sphinx-gherkindoc <sphinx-gherkindoc/README>
   tableread <tableread/README>
   artifactory

==================================================  ==============================================================================
Library Name                                        Description
==================================================  ==============================================================================
:doc:`qe_jira<qe_jira/README>`                      Quickly creates a JIRA on a QE board for testing of a JIRA from a dev board
:doc:`qecommon_tools<docs/qecommon_tools>`          A library for helper functions across QE-Tools designed for larger consumption
:doc:`qe_coverage<reporting/qe_coverage>`           A collection of tools for QE-related reporting
:doc:`github_tools<github_tools/README>`            A collection of tools around Git and GitHub to make developers' lives easier.
:doc:`sphinx-gherkindoc<sphinx-gherkindoc/README>`  A tool to convert Gherkin into Sphinx documentation
:doc:`tableread<tableread/README>`                  A library for converting reStructredText tables into Python objects
==================================================  ==============================================================================

Local Scripts
-------------

In addition to libraries that can be installed via ``pip``, this repository provides several scripts that can be utilized for various needs.

.. toctree::
   :hidden:
   :caption: Local Scripts

   etcd/ <etcd/README>
   httpbin-data/ <httpbin-data/README>

===================================================  ==================================================================================
File Name                                            Description
===================================================  ==================================================================================
check-unicode.py                                     Checks a directory structure for Unicode errors in Python, Ruby, and Feature files
:doc:`etcd/<etcd/README>`                            A collection of tools for using etcd
:doc:`httpbin-data/<httpbin-data/README>`            An enhancement to httpbin that provides data-persistent endpoints
`data_broker/`_                                      Web app to collect data from ``qe_coverage`` and forward it to the reporting tool
===================================================  ==================================================================================

.. toctree::
   :maxdepth: 2
   :caption: Metrics Standards

   Coverage Metrics <reporting/README>
   Coverage Metrics Schema <reporting/qe_coverage/coverage>
   Production Whitelist <data_broker/data/whitelist>

.. _Artifactory: https://artifacts.rackspace.net
.. _`data_broker/`: https://qetools.rax.io/coverage/doc/

.. toctree::
   :maxdepth: 2
   :caption: Contributing

   contributing
