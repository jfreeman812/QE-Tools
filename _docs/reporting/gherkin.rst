Gherkin-Based Frameworks
========================

The tools for working with the available Gherkin-based frameworks (e.g., ``behave``, ``cucumber``, ``pytest-bdd``) can be installed from :doc:`Artifactory<../artifactory>` using ``qe_coverage[gherkin]``. The extra package format is needed to ensure that ``behave`` is installed, which is used for parsing Gherkin feature files.

Tagging the Data
----------------

The coverage tooling is designed to work with the standard tagging described in the `Cucumber documentation`_ and implemented by all libraries. The :doc:`Coverage Metrics Schema<../../reporting/qe_coverage/coverage>` specifies the necessary attributes that should be added as tags. A few recommendations for tagging:

- Group together stable tags, such as polarity and priority
- Put independent Ticket ID tags as the first (outer-most) line
- Isolate status tags, with their Ticket IDs, to their own line
- When removing a status tag, move the Ticket ID tag(s) to the first (outer-most) line, adding to any existing Ticket ID tags

An example scenario that has an independent Ticket ID for when the test was created as well as being under quarantine would be:

.. code-block:: gherkin

    @TICKET-1234
    @positive @p0
    @quarantined @TICKET-2345
    Scenario: A positive test that is under quarantine

Sending the Data
----------------

After installing ``qe_coverage``, there is a single command-line script that can be used for extracting and sending the coverage data: ``coverage-gherkin``. This script does provide documentation on its use via ``coverage-gherkin -h``. This script must be run from the root of the test source tree to be parsed and only requires a single argument: the default interface type for the tests being reported on.

This script does have an optional parameter, ``--dry-run`` that can be used for validating the tags in a document tree. This will not send any data but will print out any tags that are out of compliance onto standard error and exit with a non-zero status code. If there are no problems, the script will exit with a zero status code and no additional output. This can also be useful for integrating into a Pull Request validation workflow.

``coverage-gherkin`` does work with one assumption with regard to the coverage standard: the folder hierarchy is the category hierarchy to use for coverage reporting, thus, the category tag is not required. To provide an alternate category hierarchy, the category tag will override the folder structure.

This script also has the ability to look into a sub-folder to begin parsing, via ``-p, --product-dir``. This can be useful when cloning a repository and feature files are stored in a sub-folder.

When you are ready to push data to the production dashboard, you can do so with ``--production-endpoint``. This will only succeed if all Product Hierarchies you are sending are included in the `Product Hierarchy Whitelist`_.

.. note::

   The Gherkin tooling provides a mechanism for providing "pretty" names to products and categories. When parsing a folder for feature files, if it locates a file called ``display_name.txt``, it will use the first line of this file to create the display name. Otherwise, the folder name is turned into a title-cased display name.

Reviewing the Reports
---------------------

When sending data via ``coverage-gherkin``, a URL is returned, when successful, that provides a link to the reporting tool that filters the data to show only the appropriate data. This allows the end user to confirm that the data was successfully uploaded. There is a lag between uploading and data appearing in the reporting tool so allow up to five minutes for the data to appear.

.. _`Cucumber documentation`: https://cucumber.io/docs/reference
.. _`Product Hierarchy Whitelist`: https://github.rackspace.com/QE-Metrics/data_broker/blob/master/data/whitelist.rst
