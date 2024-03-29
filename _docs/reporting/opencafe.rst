OpenCAFE Framework
==================

The tools for working with OpenCAFE can be installed from :doc:`Artifactory<../artifactory>` using ``qe_coverage``. OpenCAFE largely inherits from the Unittest framework, only overriding a few OpenCAFE specific functions. OpenCAFE specific scripts and libraries (such as ``coverage-opencafe``) call to Unittest functions and are kept to maintain compatibility with current workflows and usage.

Tagging the Data
----------------

For OpenCAFE-based teams, the tagging is managed through the ``qe_coverage`` library installed from :doc:`Artifactory<../artifactory>`. Due to the nature of setting up an OpenCAFE project, the library assumes that OpenCAFE has already been installed. Once installed, the tags can be added via ``from qe_coverage.opencafe_decorators import tags``. All necessary tagging can be done via the ``tags`` decorator by providing multiple items to the decorator. The library does provide additional decorators that are inherited from Unittest and documented in the Unittest :ref:`API Documentation<api-documentation>`.

An example of using ``tags`` to document all necessary tags::

    @tags('positive', 'TICK-123', 'p0', 'nyi', 'BUG-666', 'BUG-999')

Sending the Data
----------------

For OpenCAFE-based teams, the scripts are installed with the ``qe_coverage`` package from :doc:`Artifactory<../artifactory>`. Due to the nature of setting up an OpenCAFE project, the scripts assume that OpenCAFE has already been installed and that the tests are tagged using the methods described in `Tagging the Data`_. Once installed, there is a command-line script that can be used for extracting and sending the coverage data: ``coverage-opencafe``. This script does provide documentation on its use via ``coverage-opencafe -h``. This script must be run from the root of the test source tree to be parsed and requires three arguments: the default interface type, the product name, and the commands needed to run the tests in OpenCAFE.

This script does have an optional parameter, ``--dry-run`` that can be used for validating the tags in a document tree. This will not send any data but will print out any tags that are out of compliance onto standard error and exit with a non-zero status code. If there are no problems, the script will exit with a zero status code and no additional output. This can also be useful for integrating into a Pull Request validation workflow.

When you are ready to push data to the production dashboard, you can do so with ``--production-endpoint``. This will only succeed if all Product Hierarchies you are sending are included in the `Product Hierarchy Whitelist`_.

Reviewing the Reports
---------------------

When sending data via ``coverage-opencafe``, a URL is returned, when successful, that provides a link to the reporting tool that filters the data to show only the appropriate data. This allows the end user to confirm that the data was successfully uploaded. There is a lag between uploading and data appearing in the reporting tool so allow up to five minutes for the data to appear.

Unittest/OpenCAFE Decorators
----------------------------

Tips and Need-To-Knows
~~~~~~~~~~~~~~~~~~~~~~

1. Don't decorate test classes.

   Classes decorated with ``opencafe_decorators`` will function as expected during a normal test run, but the tests will not be included in coverage reports. In order to generate the correct coverage data, you must decorate each test (e.g., ``def test_...``, ``def ddtest_...``) individually.

#. Use the ``@unless_coverage`` decorator to avoid unnecessary setup and teardown.

   ``setUp``, ``setUpClass``, ``tearDown``, and ``tearDownClass`` methods will be executed when coverage reports are generated. By decorating these classes with ``@unless_coverage``, these methods will not be run during a coverage test run.

#. Make the coverage decorators the last executed decorators

   The coverage decorators need to be the last executed decorator on a method and should be the furthest removed from the method definition::

    @tags('positive', 'smoke', 'dropdowns')
    @data_driven_test(DropDownDataGenerator(["Settings", "Gear"]))
    def ddtest_dropdown_for(self, lnk, data):

#. Known Potential Issues

   a. **Issue 1:** You see an error during a coverage test run with ``previousClass._do_class_cleanup_tasks()`` somewhere in the traceback like this::

        ...
        previousClass._do_class_cleanup_tasks()
        ...
        AttributeError: type object 'ExampleTests' has no attribute '_class_cleanup_tasks'

      This is because the OpenCAFE test runner is looking for this attribute, which is assigned in the `setUpClass`.

      Solution: Assign the ``_class_cleanup_tasks`` attribute directly on your test fixture::

        class ExampleTests(BaseTestFixture):

            _class_cleanup_tasks = []

   #. **Issue 2:** You get a similar error to the one above, but instead for a missing ``_reporting`` attribute or something else.

      Solution: This may be because one of the setup/teardown methods was never tagged with ``@unless_coverage``. You may have to implement an empty method if one of the OpenCAFE defined setup/teardown methods is being called.::

        @unless_coverage
        def setUp(self):
            super(ExampleCafeTestFixture, self).setUp()

        @unless_coverage
        def tearDown(self):
            super(ExampleCafeTestFixture, self).tearDown()

CSV Data Injection
------------------

It is also possible to append to existing test tag data by providing information in a CSV file. This should be used
when tagging individual test methods and/or individual datasets is not specific enough. In order to use this
feature, you must use the ``--data-injection-file-path`` flag, followed by a path to your CSV file.

The format for the CSV file is as follows::

    TestClassName,test_method_name,additional_tag_1,additional_tag_2,and,so,on

Any additional tags provided in the CSV file will be appended to the specific test and reflected in the generated
coverage data.

.. include:: ../xrefs.txt
