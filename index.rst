QE-Tools
========

A collection of tools designed for use in the larger Rackspace QE Organization.


Libraries
---------

Several libraries have been created that can be installed via :doc:`Artifactory<_docs/artifactory>`.

.. note::

    Example install usage:

    .. code-block:: bash

        $ pip install -i "https://artifacts.rackspace.net/artifactory/api/pypi/pypi/simple" <LIBRARY_NAME>


.. toctree::
   :hidden:
   :caption: Libraries

   qe_jira <_docs/qe_jira/README>
   qecommon_tools <docs/qecommon_tools>
   qe_config <docs/qe_config>
   qe_coverage <_docs/reporting/qe_coverage>
   qe_logging <docs/qe_logging>
   qe_behave <_docs/qe_behave/README>
   github_tools <_docs/github_tools/README>
   sphinx-gherkindoc <_docs/sphinx-gherkindoc/README>
   tableread <_docs/tableread/README>
   _docs/artifactory

========================================================  ==============================================================================
Library Name                                              Description
========================================================  ==============================================================================
:doc:`qe_jira<_docs/qe_jira/README>`                      Quickly creates a JIRA on a QE board for testing of a JIRA from a dev board
:doc:`qecommon_tools<docs/qecommon_tools>`                A library for helper functions across QE-Tools designed for larger consumption
:doc:`qe_config<docs/qe_config>`                          A collection of tools for QE-related configuration processing.
:doc:`qe_coverage<_docs/reporting/qe_coverage>`           A collection of tools for QE-related reporting
:doc:`qe_logging<docs/qe_logging>`                        A collection of logging-related helpers to provide standard logging for QE.
:doc:`qe_behave <_docs/qe_behave/README>`                 A collection of packages and tools to support Gherkin/Behave-based testing.
:doc:`github_tools<_docs/github_tools/README>`            A collection of tools around Git and GitHub to make developers' lives easier.
:doc:`sphinx-gherkindoc<_docs/sphinx-gherkindoc/README>`  A tool to convert Gherkin into Sphinx documentation
:doc:`tableread<_docs/tableread/README>`                  A library for converting reStructredText tables into Python objects
========================================================  ==============================================================================

Local Scripts
-------------

In addition to libraries that can be installed via ``pip``, this repository provides several scripts that can be utilized for various needs.

.. toctree::
   :hidden:
   :caption: Local Scripts

   etcd/ <_docs/etcd/README>
   httpbin-data/ <_docs/httpbin-data/README>

===================================================  ==================================================================================
File Name                                            Description
===================================================  ==================================================================================
check-unicode.py                                     Checks a directory structure for Unicode errors in Python, Ruby, and Feature files
:doc:`etcd/<_docs/etcd/README>`                      A collection of tools for using etcd
:doc:`httpbin-data/<_docs/httpbin-data/README>`      An enhancement to httpbin that provides data-persistent endpoints
`data_broker/`_                                      Web app to collect data from ``qe_coverage`` and forward it to the reporting tool
===================================================  ==================================================================================

.. toctree::
   :maxdepth: 2
   :caption: Metrics Standards

   Coverage Metrics <_docs/reporting/README>
   Coverage Metrics Schema <reporting/qe_coverage/coverage>
   Production Whitelist <data_broker/data/whitelist>

.. _Artifactory: https://artifacts.rackspace.net
.. _`data_broker/`: https://qetools.rax.io/coverage/doc/

.. toctree::
   :maxdepth: 2
   :caption: Contributing

   _docs/contributing


.. toctree::
   :caption: SDLC Documents

   Overview <sdlcs/README>
   Gherkin Standards <sdlcs/gherkin-standards>
