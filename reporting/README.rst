=================
QE Coverage Tools
=================

.. sectnum::

Introduction
============

This is a collection of tools for reporting and documenting test coverage for test repositories under the control of a Rackspace QE team.

Test coverage reporting is part of the commitment of our QE organization to be driven by data.
Within the TES Technology & Data QE org, we've gone so far as to make it part of our `Table Stakes`_.

For the Rationale on why we want coverage metrics and how to apply the coverage markup to tests, please see `Coverage Metrics standard`_.

Currently we support any Gherkin-based tests, and Python OpenCAFE-based tests.
(Pytest is anticipated, but not yet supported.)

How To
======

There are two parts to the coverage reporting:

1. Annotating tests.
2. Generating and publishing coverage data.

General Tooling Notes
---------------------

The current suite of metrics tools and supporting libraries are written in Python.
Installing Python and python packages is assumed, details on doing that are out of scope for this document.
Python 2.7 and Python 3.5+ are the supported versions.

Annotating Tests
----------------

In order to gather coverage data, we need to annotate our test suites, as per the `Coverage Metrics standard`_
How tests are annotated for coverage metrics reporting depends on the automation framework being used.
This tooling supports the following frameworks:

- Gherkin-based testing: the annotations are stand-alone, you need no additional tools.
- OpenCAFE-based testing: you need to install the ``qe_coverage`` python package.
  The ``opencafe_decorators`` module in that package provides the decorators needed to annotate tests for coverage metrics gathering,
  as per the `Coverage Metrics standard`_.


Publishing Coverage Data
------------------------

Publishing - Common Details
+++++++++++++++++++++++++++

The tools in this repository scan directory trees of contain tests which have been annotated as described above.
The coverage data gathered is aggregated and sent to Splunk to handle visualization, archiving, etc.
The purpose of these tools is to automate generating and publishing coverage metrics based on the team's tests as the source of truth.
This section describes how to install and use these tools.


Tools needed:

- Python, as above.
- ``qe_coverage`` python package - Get this from `Artifactory`_.
  (For Gherkin-based coverage reporting, an additional option is needed for ``pip install``, see below.)

Reports are published to Splunk:

- The results published to Splunk include a 'host' field based on the environment variable 'JENKINS_URL'.
  'JENKINS_URL' was chosen  on the assumption/convenience that the coverage metrics reporting tool will be run on the QE team's CI server.

  - This environment variable is defined by Jenkins, so you get it 'for free' when you run the scripts to publish your reports in a Jenkins job.
  - If you need to publish from another source, you need to arrange for this environment variable to be set properly before you run the report.
  - If this variable is not set, some form of the hostname of the current machine will be used. This may not be what you want/expect.

- The authentication needed to successfully publish to Splunk is a token that is passed via a command-line switch to all the publishing scripts.

  - When publishing from Jenkins, this token should be configured in your server so that the job using it *does not*, and *should not* hard code this value.

Common Coverage annotations:

- Defaulting ``Interface Type`` - It would be very tedious and repetitive to have to specify the interface type on each test.

  - As such, all our tooling provides a way to default that, either by how it analyzes the test directory structure, or via command line switch.
    See the ``--help`` for each tool for details

- Similarly with ``Product``: to avoid tedious repetion in the test source annotations, the tooling itself provides defaults for that as well.

Publishing Gherkin Coverage Data
++++++++++++++++++++++++++++++++

For Gherkin-based tests (whether based on the Python ``behave`` test runner or the Ruby ``cucumber`` runner),
the tooling is able to do static analysis on the source files.
The tool used for Gherkin reporting is ``coverage-gherkin`` (implemented by ``qe_coverage/gherkin.py``)
and details on exactly how to invoke that script can be found using the ``--help`` switch.

  NOTE: While the coverage reports can be generated from any Gherkin sources, this tooling using Python (as above) and ``qe_coverage`` should be installed with the ``gherkin`` option.
  This will install a special version of ``behave``, used to parse the Gherkin.
  (It is special because the released version of ``behave``'s parser cannot yet handle the forms used by ``cucumber``.)

  NOTE: The tooling is designed to be installed and used in to a clean Python virtual environment, so these extra packages can be isolated from your normal test environment(s).


Publishing OpenCAFE Coverage Data
+++++++++++++++++++++++++++++++++

For OpenCAFE-based tests, the publishing process is a little more involved.
Due to the nature of how data generated testing is done in OpenCAFE,
static analysis of the sources does not provide the full story of coverage.
Thus, OpenCAFE coverage metrics are gathered in two steps:

1. A special OpenCAFE test run is made that uses the OpenCAFE-aware decorators (see above) to gather the test coverage data.
2. The data from the previous run is then processed and published.

Both of those steps are implemented in one script: ``coverage-opencafe`` (implemented by ``qe_coverage/collect_opencafe_coverage.py``).
and details on exactly how to invoke that script can be found using the ``--help`` switch.

(Note that ``coverage-send-opencafe-report`` is a helper script installed to handle step 2, but is intended for use by ``coverage-opencafe`` only.)

Because a full-test run is needed, the metrics gathering and reporting for OpenCAFE needs to be done within a project's existing infrastructure.
Since the ``qe_coverage`` module is needed for the ``opencafe_decorators`` already, the actual reporting scripts impose no additional requirements or installations.
Note: When using the ``coverage-opencafe`` tool do not limit the run with any tags or other controls so that the full coverage will be generated.

Tips and Need-To-Knows for Decorating OpenCAFE Tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Don't decorate test classes.

Classes decorated with ``opencafe_decorators`` will function as expected during a normal test run, but the tests will not be included in coverage reports.
In order to generate the correct coverage data, you must decorate each tag individually.

2. Use the ``@unless_coverage`` decorator to avoid unnecessary setup and teardown.

``setUp``, ``setUpClass``, ``tearDown``, and ``tearDownClass`` methods will be executed when coverage reports are generated. By decorating these classes with
``@unless_coverage``, these methods will not be run during a coverage test run.

3. Known Potential Issues

**Issue 1:** You see an error during a coverage test run with ``previousClass._do_class_cleanup_tasks()`` somewhere in the traceback like this::

    ...
    previousClass._do_class_cleanup_tasks()
    ...
    AttributeError: type object 'ExampleTests' has no attribute '_class_cleanup_tasks'

This is because the OpenCAFE test runner is looking for this attribute, which is assigned in the `setUpClass`.

Solution: Assign the ``_class_cleanup_tasks`` attribute directly on your test fixture::

    class ExampleTests(BaseTestFixture):

        _class_cleanup_tasks = []

**Issue 2:** You get a similar error to the one above, but instead for a missing ``_reporting`` attribute or something else.

Solution: This may be because one of the setup/teardown methods was never tagged with ``@unless_coverage``. You may have to implement an empty method
if one of the OpenCAFE defined setup/teardown methods is being called.::

    @unless_coverage
    def setUp(self):
        super(DCXQEBaseTestFixture, self).setUp()

    @unless_coverage
    def tearDown(self):
        super(DCXQEBaseTestFixture, self).tearDown()

.. _Coverage Metrics standard: qe_coverage/coverage.rst
.. _Table Stakes: https://one.rackspace.com/pages/viewpage.action?title=Table+Stakes+Definition&spaceKey=cloudqe
.. _Artifactory: https://artifacts.rackspace.net
