How to Contribute
=================

All contributions are greatly appreciated and welcome!

We are looking for contrbutions that add new packages as well as those that
improve/enhance/bug-fix existing packages!
We are also very open to preliminary version 0.1 packages;
those have less stringent requirements due to their initial / draft nature.

Contribution and Workflow Standards
-----------------------------------

To maintain standards and ease code review,
we follow the processes as describe in our very own :doc:`SDLC Documents<../sdlcs/README>`,
with some refinements.
Refinements?
Wait, if you want everyone else to use that SDLC, why aren't you using it here?
We are! The packages in this repo are intended for use by many other teams;
based on that larger scope and responsibility, our SDLC is slightly more `stringent` than might
be appropriate for any individual QE team.
Our refinements are a little bit about code and a bit more about the Pull Request (PR) process:


  * The Code Itself:

    * Documentation: A must-have.
      We follow the Google `napolean documentation standard`_.
      See our existing package documentation for examples as well.
    * Self-tests: A very-strong-want-to-have.
      PRs with code changes should make a reasonable attempt to add tests for new/revised code.


  * The PR process:

    * PRs need three reviewers' approvals to merge, but can make it through with two:

        * After second reviewer signed off, any third reviewer has 24 hours to chime in.
          After 24 hours, a PR can be merged with only two reviewers' approval.
        * Trivial Pull Requests (e.g., fixing a typo or making a private method public
          for a future Pull Request) may be "First Review, First Merge" (FRFM)
          if the author and first reviewer concur.

    * Review/Change workflow:

        * Assign new PRs to as many members of the QE Tools Contributors team as possible.
          PRs previously discussed with a specific person may be assigned to them directy to start.
        * When starting a review, prune the assignee list to just yourself to avoid duplicate effort.
        * Once engaged, a reviewer has 48 hours to respond to changes
          before the changes are considered approved.
        * Once completed reviewing:

            * If approving or if just commenting,
              un-assign yourself and assign to any remaining members of the QE Tools Contributors team.
            * If requesting changes, assign the PR back to the author.

        * As an author, once requested edits are completed,
          un-assign yourself and assign to the reviewer requesting the feedback;
          If the change is large enough and other individuals have already reviewed,
          you may re-assign to them and ask for an additional review, but it is not required.

    * Fast Follows (FF): Sometimes reviewers will accept / merge changes upon condition of a FF PR.
      FF is usually used when additional changes will cause a lot of diff noise, or otherwise make
      the current PR harder to understand, `without` making significant changes
      to the functioning of the code.
      When a PR is merged with a FF request, the author is expected to submit the FF PR quickly.
      This should not be difficult as changes deferred to a FF PR should not be substantial.


Documentation Review
--------------------

Documentation for this repo is built with the ``_docs/build-docs.py`` script.
Documentation builds have additional Python packaging requirements.
When running that script for the first time in a virtual environment, 
use the ``--setup`` command-line parameter to make sure all the necessary packages are installed.
The built documents will be in the ``docs`` directory.
Typically you can open the ``docs/index.html`` file to browse the documentation.

This repo has an automatic PR checker job that will also build the documentation and post a link
to it in the comments for any submitted or updated PR.
Reviewers are free to pull the PR and build the docs but it is usually easier to wait for this
job to run and just view the documents at the link it posts.



.. _contributing: https://github.rackspace.com/dcx/dcxqe-common/blob/master/CONTRIBUTING.md
.. _SDLC: https://pages.github.rackspace.com/AutomationServices/RBA-QE-Common/sdlc.html#code-management
.. _`napolean documentation standard`: http://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html
