QE Coverage Metrics
===================

The Rackspace QE team has worked to create a standard for tracking the coverage for a product under test.

Rationale
---------

Developing and utilizing a standard schema and tooling around coverage data allows for clear and consistent communication within individual teams as well as across teams, business units, and Rackspace. This standardization effort allows for standard reporting to be created that can help leadership understand the coverage for products as well as identify gaps in coverage and recognize risks, such as tests under quarantine. It also allows for historical reporting to see recent trends as well as trends over time.

Getting Started
---------------

In order to fully participate in the QE Coverage Metrics, there are three main areas of interest:

#. Tagging the Data - The tagging for the QE Coverage Metrics follows a specific set of defined attributes that should be assigned to tests. The schema is located in the :doc:`Coverage Metrics Schema<qe_coverage/coverage>`.
#. Sending the Data - The data may be compiled and sent using a variety of tooling, depending on the underlying framework. The documentation for these tools is located in :doc:`qe_coverage<qe_coverage>`.
#. Reviewing the Reports - The reports can be viewed online by following the following link: https://rax.io/qe-coverage-metrics

Implementation
--------------

To begin using QE Coverage Metrics, the requested workflow is outlined below. This workflow is to not only ensure that tooling works as expected, but to provide consistent data to the overall coverage of all products under test.

#. Use appropriate tooling for the underlying framework, or :doc:`contribute support<../contributing>` for the framework in use.

#. Tag existing tests as outlined in :doc:`Coverage Metrics Schema<qe_coverage/coverage>`.

#. Review data provided by running coverage with the ``--dry-run`` option in collecting data.

#. Consult with the ``QE Coverage`` team in Slack in ``#qe-tools`` or via email at ``qe-tools-contributors@rackspace.com`` for final approval and sign-off before sending collected data to the production Splunk instance.