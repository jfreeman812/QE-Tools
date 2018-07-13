qe_behave
=========

This package represents common tools and dependencies for use by QE Teams using the Python ``behave`` testing framework.

.. note:: This is intended as a Python 3-only package.

Packages Installed
------------------

This package primarily exists as a way to conveniently gather together a set of useful packages for
both writing tests, and for the accompanying tooling. By installing this package you will get a known set
of packages that work well together. You may use this as is, or as a jumping-off point for your own
additional changes, customizations, etc.

.. note:: See the linked documentation for each package for its nitty-gritty details, including dependencies.


General Testing
~~~~~~~~~~~~~~~

These packages are included for enhancing all of our testing, alongside `behave`_ itself:

    * :doc:`qecommon_tools<../../docs/qecommon_tools>` - A collection of generally useful tools leveraged here, and by other QE-Tools projects; it is called out here to encourage use outside of just QE-Tools, and to elict contributions, improvements, etc.
    * :doc:`qe_config<../../docs/qe_config>` - contains helper functions for managing config files across multiple related test environments.
    * :doc:`qe_logging<../../docs/qe_logging>` - contains ``behave_logging`` for clarity of ``behave`` tests, as well as additional capabilities for standardizing and simplifying logging in general.


UI Testing
~~~~~~~~~~

Install ``qe_behave`` with the ``[UI]`` option to get these:

    * `selenium`_  - base python selenium package
    * :doc:`selenium_extras<../../docs/selenium_extras>` - helpers for making selenium-based testing easier.


API Testing
~~~~~~~~~~~

Install ``qe_behave`` with the ``[API]`` option to get these:

    * `requests`_ - base python requests package

Also, :doc:`qe_logging<../../docs/qe_logging>` - (Part of General Testing) contains :py:mod:`requests_client_logging<qe_logging.requests_client_logging>`
which has some nice extra features (not just logging) as well.


Tooling
~~~~~~~

Installing this package will get you the common set of tools as well:

    * :doc:`qe_coverage<../../_docs/reporting/qe_coverage>` - the ``behave`` coverage reporting tool - can also be used for Gherkin tag checking in dry-run mode
    * :doc:`sphinx-gherkindoc<../../_docs/sphinx-gherkindoc/README>` - convert Gherkin into nice readable Sphinx documentation
    * `flake8`_, `flake8-builtins`_, and `flake8-tuple`_  - Python code checking


Recommended Extra Packages
~~~~~~~~~~~~~~~~~~~~~~~~~~

We strongly recommend you also install and configure:

    * :doc:`github_tools<../../_docs/github_tools/README>` - for local git commit hooks and Jenkins PR Checking Jobs

.. include:: ../xrefs.txt
