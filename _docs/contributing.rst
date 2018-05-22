How to Contribute
=================

Contributions are greatly appreciated. To maintain standards and ease code review, the following is recommended.

Contribution Standards
----------------------

To ensure following repo standards and easing code review, QE-Tools follows the DCXQE contributing_ standards. This document includes git, code review, docstring, and pep standards of the repo.

Workflow Standards
------------------

Further detail of Code Management, Git Workflow, and Pull Request Workflow is outlined in RBA-QE's SDLC_.

Self Check
----------

After following the standards as given in the documentation links above, if the QE-Tools :doc:`git-hooks <github_tools/README>` are not installed a self check can be run from the root directory of QE-Tools via ``./self-check.sh``.

Documentation Review
--------------------

After successful execution of ``./self-check.sh`` (or running the ``self-check.sh`` included in the ``_docs`` directory), documentation will be built and available in the ``docs`` folder of the QE-Tools root. The documentation can also be reviewed after a successful check run by Jenkins on the creation of a PR, by following the "Docs Link" link comment that is auto-posted on the PR.

.. _contributing: https://github.rackspace.com/dcx/dcxqe-common/blob/master/CONTRIBUTING.md
.. _SDLC: https://pages.github.rackspace.com/AutomationServices/RBA-QE-Common/sdlc.html#code-management
