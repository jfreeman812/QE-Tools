How to contribute
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

After following the standards as given in the documentation links above, if the QE-Tools git-hooks_ are not installed a self check can be run from the root directory of QE-Tools via ``./self-check.sh``.

Documentation Review
--------------------

After successful execution of ``./self-check.sh`` (or running the ``self-check.sh`` included in the _docs directory), documentation will be built and available in the ``docs`` folder of the QE-Tools root. The documentation can also be reviewed after a successful check run by Jenkins on the creation of a PR, by viewing the URL ``https://jenkinsqe.rba.rackspace.com/job/Check_QE_Tools_PRs/<BUILD_NUMBER>/HTML_Report/`` (the BUILD_NUMBER is available in the details of the ``default`` check on the created pull request).

.. _contributing: https://github.rackspace.com/dcx/dcxqe-common/blob/master/CONTRIBUTING.md
.. _SDLC: https://pages.github.rackspace.com/AutomationServices/RBA-QE-Common/sdlc.html#code-management
.. _git-hooks: https://pages.github.rackspace.com/QualityEngineering/QE-Tools/github_tools/README.html#gt-install-hooks