qe_behave
=========

This package represents common tools and dependencies for use by QE Teams using the Python 'behave' testing framework.

.. note:: This is intended as a Python3 package only.

Packages installed
-------------------

This package primarily exists as a way to conveniently package together a set of other useful packages for
both writing tests and for the accompanying tooling. By installing this package you will get a known set
of packages that will work well together. You may use this as is, or as a jumping off point for your own
additional changes, customizations, etc. For nitty gritty details, please see the documention for each of the packages.

.. note:: The packages installed here have their own dependencies, see the relevent documentation for those packages for details.


General Testing
~~~~~~~~~~~~~~~

These packages for general use when writing tests, along with `behave`_ itself:

    * :doc:`qecommon_tools<../../docs/qecommon_tools>` - generally useful Python common tools, needed by other packages here,
      but we are calling it out specifically to encourage use and contributions
    * :doc:`qe_logging<../../docs/qe_logging>` - contains a behave_logging module and a low-level requests_logging module.


UI Testing
~~~~~~~~~~

Install ``qe_behave`` with the ``[UI]`` option to get these:

    * `selenium`_  - base python selenium package
    * <Forthcoming> - UI testing on top of selenium


API Testing
~~~~~~~~~~~

Install ``qe_behave`` with the ``[API]`` option to get these:

    * <Forthcoming> - API testing on top of requests


Tooling
~~~~~~~

Installing this package will get you the common set of tools as well:

    * :doc:`qe_coverage<../../_docs/reporting/qe_coverage>` - the behave coverage reporting tool - can also be used for Gherkin tag checking in dry-run mode
    * :doc:`sphinx-gherkindoc<../../_docs/sphinx-gherkindoc/README>` - convert Gherkin into nice readable Sphinx documentation
    * `flake8`_, `flake8-builtins`_, and `flake8-tuple`_  - Python code checking


Recommended Extra Packages
~~~~~~~~~~~~~~~~~~~~~~~~~~

We strongly recommend you also install and configure:

    * :doc:`github_tools<../../_docs/github_tools/README>` - for local git commit hooks and Jenkins PR Checking Jobs

.. _behave: https://github.com/behave/behave
.. _selenium: https://pypi.org/project/selenium/
.. _flake8: https://pypi.org/project/flake8/
.. _flake8-builtins: https://pypi.org/project/flake8-builtins/
.. _flake8-tuple: https://pypi.org/project/flake8_tuple/
