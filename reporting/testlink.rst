TestLink
========

The tools for working with TestLink can be installed from :doc:`Artifactory<../artifactory>` using ``qe_coverage``.

Tagging the Data
----------------

The :doc:`Coverage Metrics Schema<qe_coverage/coverage>` specifies the necessary attributes that should be added as tags. Specifics for adding these attributes within TestLink are as follows:

- Categories are derived from the test suite hierarchy (which has three levels at most)
- Tags are collected from the custom Keywords associated with each test.
- Tags that are not a part of the schema are ignored. The defaults from the schema are applied when generating the coverage from TestLink as well.
- Unless a keyword specifying "automated" is used, all test cases will have the **Execution Method** set to "manual".
- **Test Name** comes from the test's **Test Case Title**.
- **Product** is specified on the command line of the ``coverage-testlink`` tool

Sending the Data
----------------

After installing ``qe_coverage``, there is a single command-line script that can be used for sending the coverage data: ``coverage-testlink``. This script does provide documentation on its use via ``coverage-testlink -h``. This script requires three parameters. The first is ``testlink_xml_file``, which is the path to the XML export file from a TestLink test suite. The second is ``product_name``, which is the product name for the coverage report. The final parameter is the default interface type, which is either ``gui`` or ``api``.

.. note::

    The TestLink export must have the **Export with Keywords** check-box checked.

.. note::

   If the test hierarchy coverage multiple products, it will be necessary to export just the level corresponding to one product and run the ``coverage-testlink`` for that product and repeat as needed.

This script does have an optional parameter, ``--dry-run`` that can be used for validating the tags in a document tree. This will not send any data but will print out any tags that are out of compliance onto standard error and exit with a non-zero status code. If there are no problems, the script will exit with a zero status code and no additional output.

The script also has the ability to skip past categories. For example, if the first category is the product name, that category should be skipped. The optional parameter is ``--leading-categories-to-strip`` and takes an integer for the number of categories to skip.

Reviewing the Reports
---------------------

When sending data via ``coverage-testlink``, a URL is returned, when successful, that provides a link to the reporting tool that filters the data to show only the appropriate data. This allows the end user to confirm that the data was successfully uploaded. There is a lag between uploading and data appearing in the reporting tool so allow up to five minutes for the data to appear.
