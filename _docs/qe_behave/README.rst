qe_behave
=========

This package represents common tools and dependencies for use by QE Teams using the Python 'behave' testing framework.
NOTE: This is a Python3 package only.

Installing this package will get you the suggested set of packages to use, along with behave itself:

    * :doc:`qecommon_tools<../../docs/qecommon_tools>` - generally useful Python common tools, needed by other packages here,
      but calling it out specifically because we want to encourage use.
    * :doc:`qe_logging<../../docs/qe_logging>` - contains the behave_logging module
    * :doc:`qe_coverage<../../_docs/reporting/qe_coverage>` - contains the behave coverage reporting tool.
    * :doc:`sphinx-gherkindoc<../../_docs/sphinx-gherkindoc/README>` - sphinx-gherkindoc script for turning your feature files into sphinx for nicely formatted documentation.

If you are doing UI testing with Selenium, we suggested you use the `TBD` package for that.

API testing should use the soon to be released `qe_requests` (or whatever we are going to call it)
