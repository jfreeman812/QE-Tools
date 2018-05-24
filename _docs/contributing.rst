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

Operational Details - Quick Start
---------------------------------

* Pull Request Guidelines:

    * Pull Requests should be atomic and as small as possible to accomplish what is needed. If there is a need to change multiple things, please split it into multiple Pull Requests.
    * Pull Requests should have a minimum of two reviews, with a preference for three.

        * Once two reviewers have approved the Pull Request, any additional reviewers have 24 hours in which to submit their reviews or to pass on the review. If no additional reviewers respond within the 24-hour window, or they choose to pass, the Pull Request may be merged with only two approvals.

    * Once engaging in a review, a reviewer has 48 hours to re-visit a review after the author has made the necessary changes. Any review that sits idle with a reviewer for over 48 hours will be considered approved by that reviewer.
    * All packages should have self-tests. Any new Pull Request with code changes should make a reasonable attempt to add tests for the new code.

* Pull Request Procedure:

    * When creating a pull request, assign to as many members of the QE Tools Contributors team as possible. If you have previous discussed with a member of the team doing the first review, you may assign to them directly.
    * When starting a review, change the assignee list to yourself to prevent duplicate efforts.
    * Once completed reviewing:

        * If approving or just commenting, un-assign yourself and assign to any remaining members of the QE Tools Contributors team.
        * If requesting changes, assign the Pull Request Back to the author.

    * As an author, once requested edits are completed, un-assign yourself and assign to the reviewer requesting the feedback.

        * If the change is large enough and other individuals have already reviewed, you may re-assign to them and ask for an additional review, but it is not required.

.. note::
    For trivial Pull Requests (e.g., fixing a typo or making a private method public for a future Pull Request) may be "First Review, First Merge" (FRFM) if the author and first reviewer concur.

.. note::
    A Pull Request might be merged with requests for changes in a Fast-Follow (FF) Pull Request. This is often done when the changes would complicate the current Pull Request, such as renaming a heavily-used method or documentation cleanup separate from the code. For FF Pull Requests, the original author is expected to submit the follow up Pull Request quickly.

Documentation Review
--------------------

After successful execution of ``./self-check.sh`` (or running the ``self-check.sh`` included in the ``_docs`` directory), documentation will be built and available in the ``docs`` folder of the QE-Tools root. The documentation can also be reviewed after a successful check run by Jenkins on the creation of a PR, by following the "Docs Link" link comment that is auto-posted on the PR.

.. _contributing: https://github.rackspace.com/dcx/dcxqe-common/blob/master/CONTRIBUTING.md
.. _SDLC: https://pages.github.rackspace.com/AutomationServices/RBA-QE-Common/sdlc.html#code-management
