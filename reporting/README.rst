Introduction
============

This is a collection of tools for reporting and documenting test coverage for repositories under the control of a Rackspace QE team.

Test coverage reporting is an essential part of QE activities, allowing us to assess the overall state of the testing for the various products we support.
There are two parts to coverage reporting:

1. Annotating our tests
2. Generating and publishing the coverage data.

Annotating Our Tests
--------------------

Motivation for, and details of, the kinds of coverage metrics we gather,
as well as how we annotate our tests to gather it, can be found in the `Coverage Metrics standard`_


Publishing Coverage Data
------------------------

As of this writing (2018Q1), we support Gherkin-based and OpenCAFE-based test reporting.
PyTest is on the radar but not yet assessed or supported.

Publishing Coverage Data - Common Details
+++++++++++++++++++++++++++++++++++++++++
For all of our coverage tools, there are some common elements:

- Reports are published to Splunk.
    (ed. note: do we want/need Splunk URL here? I hope not, it's already in code...)
- The results per QE team are recorded under the fully-qualified domain-name of the QE team's Jenkins CI server.
- This server name is "passed to" the coverage reporting scripts via the JENKINS_URL environment variable.

  - This environment variable is defined by Jenkins, so you get it 'for free' when you run the scripts to publish your reports in a Jenkins job.
  - If you need to publish from another source, you need to arrange for this environment variable to be set properly before you run the report.

- The authentication needed to successfully publish to Splunk is a token that is passed via a command-line switch to all the publishing scripts.

  - This token should be configured in your Jenkins server so that the Jenkins job that generates the reports *does not*, and *should not* hard code this value.

- Defaulting ``Interface Type`` - It would be very tedious and repetitive to have to specify the interface type on each test.

  - As such, all our tooling provides a way to default that, either by how it analyzes the test directory structure, or via command line switch.
    See the ``--help`` for each tool for details

- Similarly with ``Product`` and ``Project`` Information, to avoid tedious repetion, all the tooling provides ways to default this information.

Publishing Gherkin Coverage Data
++++++++++++++++++++++++++++++++

For Gherkin-based tests (whether based on the Python behave test runner or the Ruby cucumber runner),
the tooling is able to do static analysis on the source files. The tool used for Gherkin reporting
is ``qe_coverage/gherkin.py`` and details on exactly how to invoke that script can be found using the ``--help`` switch.


Publishing OpenCAFE Coverage Data
+++++++++++++++++++++++++++++++++
    (ed. note: There is another PR outstanding that adds in the OpenCAFE tools,
    when that lands, this PR will be updated with the specific details of how to do these steps)

For OpenCAFE-based tests, the process is a little more involved.
Due to the nature of how data generated testing is done in OpenCAFE,
static analysis of the sources does not provide the full story of coverage.
OpenCAFE coverage metrics are gathered in two steps:

1. A special OpenCAFE test run is made that uses the OpenCAFE-aware decorators to gather the test coverage data.
     See ``script-name-per-PR-not-yet-merged-per-editorial-note-above``
2. The data from the previous run is then processed and published.
     See ``script-name-per-PR-not-yet-merged-per-editorial-note-above``


.. _Coverage Metrics standard: qe_coverage/coverage.rst
