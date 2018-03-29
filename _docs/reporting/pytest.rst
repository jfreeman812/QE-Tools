Pytest Framework
================

The tools for working with Pytest can be installed from :doc:`Artifactory<../artifactory>` using ``qe_coverage``. Pytest integration does not require adding imports to test cases.
Integration is completed via installing pytest functionality as a pytest plugin. Once installed, tags can be view via ``pytest --markers``, and command line options for running can be found in the ``qe_coverage`` section when running ``pytest --help``.

Tagging the Data
----------------

For Pytest-based teams, the tagging is managed through the ``pytest qe-coverage`` plugin installed from :doc:`Artifactory<../artifactory>`. Once installed, the tags can be added via ``@pytest.mark.tags`` or other relevant ``@pytest.mark.<TAG>`` tag. All necessary tagging can be done via the ``@pytest.mark.tags`` decorator by providing multiple items to the decorator. The library does provide additional decorators that are documented in :ref:`API Documentation<api-documentation>`.

An example of using ``@pytest.mark.tags`` to document all necessary tags::

    @pytest.mark.tags('positive', 'TICK-123', 'p0', 'nyi', 'BUG-666', 'BUG-999')

Sending the Data
----------------

For Pytest-based teams, the pytest plugin is installed with the ``qe_coverage`` package from :doc:`Artifactory<../artifactory>`. The plugin assumes that the tests are tagged using the methods described in `Tagging the Data`_. Once installed, there are multiple options within the ``qe_coverage`` section available via ``pytest --help`` that can be used for extracting and sending the coverage data. The ``pytest`` command can be run as done prior to ``qe_coverage`` integration, though it does require the new arguments provided from the plugin to gather and send data.

The pytest options do include an optional parameter, ``--dry-run``, which allows for validating the tags in a document tree. Also the ``--preserve-files`` parameter will create coverage metrics in the expected schema, with the location of the created files being displayed at the end of the run. These can be reviewed for valid data prior to data being sent.

When you are ready to push data to the production dashboard, you can do so with ``--production-endpoint``. This will only succeed if all Product Hierarchies you are sending are included in the :doc:`Product Hierarchy Whitelist<../../data_broker/data/whitelist>`.

Reviewing the Reports
---------------------

When sending data via with the proper arguments, a URL is returned, when successful, that provides a link to the reporting tool that filters the data to show only the appropriate data. This allows the end user to confirm that the data was successfully uploaded. There is a lag between uploading and data appearing in the reporting tool so allow up to five minutes for the data to appear.

Pytest Decorators
-----------------

.. _api-pytest-documentation:

API Documentation
~~~~~~~~~~~~~~~~~

.. automodule:: qe_coverage.pytest_coverage
    :members:
    :undoc-members:
    :show-inheritance:
