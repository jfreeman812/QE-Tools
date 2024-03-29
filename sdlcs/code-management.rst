Code Management
===============

We use Git (tool) and GitHub (platform)
to track and coordinate aspects of the SDLC
in an effort to promote team development
and ease automation of tasks such as deployments.
We maintain a public repository with a single master branch.
Each developer should create an account-level fork of that repository
and clone that fork locally for development.
Developers should submit changes via Pull Request for review and integration.
For more information on why we use Forks and Pull Requests instead of branches,
please see `Git Branches Considered Harmful`_.

Repository Conventions
----------------------

* Each repository should have, in the top level directory:

  * ``README.md`` or ``README.rst`` explaining what it is,
    who the audience is, etc.
    If applicable,
    this can simply be a link to the documentation built
    from a documentation tool. (See the ``README.rst`` for `this repository`_ as an example)

  * ``env-setup`` an executable script that sets up the environment

    * to be run by humans at will
    * to be run (indirectly) via automation tooling (such as Jenkins or Travis CI)
    * will fail if it is not running in a virtual environment (when appropriate)
    * otherwise will install
      and configure the environment for testing

  * ``self-check`` an executable script that does a self-check on the repository.

    * to be run by humans at will (such as before pull requests)
    * to be run by automation tooling for pull request acceptance testing.
    * This script should support a --setup command line parameter
      which will invoke the env-setup script
      to make sure the environment is good
      before running self-check logic.

    * automation tooling must always pass the --setup parameter
      to ensure the environment is up to date.

  * ``run-tests`` an executable script that handles the boilerplate of running tests:

    * to be run by humans at will
    * to be run by automation tooling for regular runs of test jobs
    * this script should support a --check command line parameter
      which will invoke the self-check script with the --setup option
      to make sure the environment is good
      and the self-checks all pass

    * this script should accept arbitrary parameters
      and pass them to the test framework.

.. note::
   For the executable scripts,
   use the appropriate language
   and extension for your environment.

* Each repository should also use the appropriate documentation tools
  for creating documentation for the code and test cases (e.g., Sphinx for Python)


General Code Management Policies
--------------------------------

Commit Management
~~~~~~~~~~~~~~~~~

Commits should be smaller,
related commits rather than large and monolithic.
Do not lump together unrelated code into a single commit,
unless requested to squash a pull request by a reviewer.

Commit Messages
~~~~~~~~~~~~~~~

When doing a commit,
there is a specific format to follow.
The commit should contain a summary and a description.
The title should be no more than 50 characters in length.
It is recommended,
although not required,
to utilize the prefixes found in `Work: Create Pull Request`_.
The description should contain a more detailed explanation of the change.
The description should word wrap at 72 lines as well.
For additional information about the message format,
see `A Note About Git Commit Messages`_.

.. note::
   If the pull request has only one commit,
   GitHub uses the commit message to try and pre-populate the title and comment.
   By following the suggested format above,
   the pull request title
   and comment should need minimal changes.
   If the prefix is used,
   the pull request title will have it
   which is where the prefix **is** required.

Git Workflow
------------

* `Setup: Fork and Clone`_
* `Work: Branch Management`_
* `Collaborate: Review`_

Setup: Fork and Clone
~~~~~~~~~~~~~~~~~~~~~

To develop for QE,
create a fork of the organizational repository in your personal account
and clone that fork locally as documented in `Fork A Repo`_.

.. note::
   To prevent accidentally pushing to the upstream repository,
   update the update push URL to a non-valid URL.
   We recommend using DISABLE as a visual indicator::

        git remote set-url --push upstream DISABLE

   This change to the upstream push URL is a secondary defense
   because the master branch for the upstream repository should be set
   as a protected branch to disable pushing.

Branching Policy
----------------

The main repository has one,
and only one,
coding branch: ``master``.
There *can* be a second branch,
``gh-pages``,
that is a detached branch used for documentation.
Branching is supported
and required on all personal account forks.
All pull requests (below) need to come from independent branches
in a personal fork to the master branch on the main repository.

Pull Request (PR) Workflow
--------------------------

A pull request is the process for transitioning code
from a personal fork to the master repository.
A pull request is a feature of GitHub that allows for
collaboration on a proposed changed to the repository.

At its core a pull request needs to meet three criteria:

* Conforms to all coding standards
* Makes a useful change
* Doesn't break anything

Work: Branch Management
~~~~~~~~~~~~~~~~~~~~~~~

While a pull request can be submitted from *any* branch,
we recommend creating a topic branch.
That keeps the work atomic
and allows for changes to easily be committed
and pushed to the branch
and GitHub will automatically update the pull request.
A suggested workflow for starting a branch is::

    git checkout master
    git pull upstream master       # Bring in the latest upstream code to minimize chance of merge conflict
    git checkout -b <BRANCH_NAME>  # Checkout <BRANCH_NAME> after creating it

As development occurs,
commits should be made to the branch.
For details on commits,
see `Commit Management`_.
Once a branch is ready for submission as a pull request,
it must be pushed to the personal repository::

    git push origin <BRANCH_NAME>

.. note::
   There is nothing that precludes pushing
   to the personal repository more frequently;
   it just is required for submitting a pull request.
   It is suggested to start pushing early
   and often as a part of the development process
   to minimize the code residing locally only.

Work: Create Pull Request
~~~~~~~~~~~~~~~~~~~~~~~~~

A pull request should be feature complete upon submission.
The submission of a pull request indicates that the code has been finished
and confirmed functioning.
Once a pull request has been created
it is a signal to the reviewers to begin reviewing.
The pull request process is detailed in `Creating a pull request from a fork`_.
Note that the *head fork* is the personal repository fork.

As mentioned in `Work: Branch Management`_,
by submitting each pull request from independent branches,
it ensures each pull request remains independent
and minimizes merge conflicts.

Each pull request must have a title and a comment.
These should conform to the standards
described in `Commit Messages`_ with one addition:
the title must be in the format of
``<Prefix>: <Title>`` where ``<Prefix>`` is one of the following:

============  ==========================================================================
Prefix        | Use Case
============  ==========================================================================
<JIRA_ID>     | Any commit related to a specific JIRA
Enhancement   | Any enhancement outside of JIRA (should be small changes)
FF            | A fast follow for a previous pull request (usually small very specific
              | changes, expected to be completed quickly after the pull request merges)
DO NOT MERGE  | A pull request that should not be merged (e.g., may break functionality,
              | opened for debugging or discussion)
Spike         | A proof-of-concept that may not be merged as-is; can include a JIRA ID
============  ==========================================================================

A pull request should contain a single unit of work.
The pull request should only add, remove, or change
one feature / group of features.
Do not bundle features together.
Changes that need to be made
across multiple repositories are acceptable,
but reference the partnering pull requests within each other.
To quote the `Linux kernel submission guidelines`_:

    For example, if your changes include both bug fixes
    and performance enhancements for a single driver,
    separate those changes into two or more patches.
    If your changes include an API update,
    and a new driver which uses that new API,
    separate those into two pull requests.

    On the other hand,
    if you make a single change to numerous files,
    group those changes into a single pull request.
    Thus a single logical change
    is contained within a single pull request.

    The point to remember is
    that each pull request should make
    an easily understood change
    that can be verified by reviewers.
    Each pull request should be justifiable
    on its own merits.

The final step before creating a pull request
is to assign the appropriate reviewers.
See `Collaborate: Review`_ to help determine
the appropriate first reviewer(s).

.. admonition:: Additional pull request support
   :class: note

   Depending on the nature of the pull request,
   the automatic Jenkins pull request checker may not be sufficient
   to demonstrate that the code is working.
   In those cases,
   the pull request should be executed
   against the source system if possible
   in a Jenkins job
   and the job URL should be added
   to the pull request as a comment.
   If there are any failures in the job,
   include the appropriate explanation
   if the failure is acceptable
   (e.g., a test needs to be quarantined but is not included in this pull request).
   If needed, the Jenkins job can be re-run
   and additional links added
   to demonstrate the problem is at a system level
   and not related to the pull request.

.. admonition:: Merge Conflicts
   :class: note

   Any pull request submitted needs to merge-able from the onset.
   When submitting a pull request,
   GitHub will issue a warning if a merge conflict exists:

    .. image:: _static/bad_merge.png

   While GitHub will allow the pull request to be created,
   do not submit the pull request
   until the problem has been resolved.
   Sometimes a simple merge against the master branch is sufficient.
   There are times when a pull request may build on another pull request
   and require the other pull request to be resolved first.
   In those cases,
   indicate that status in the dependent pull request comments
   to avoid merge issues and ensure pull requests are reviewed
   and merged in the correct order.

   If a completed merge causes an existing pull request
   to have conflicts, try running::

        git checkout <BRANCH_NAME>
        git pull upstream master
        git push origin <BRANCH_NAME>

   If that is unsuccessful,
   a rebase_ may be necessary.

Collaborate: Review
~~~~~~~~~~~~~~~~~~~

Any pull request submission needs to be reviewed
by at one least one person.
The final reviewer is responsible
for merging the pull request.

Once a pull request is ready,
assign all eligible members for review.
This can be tweaked if there is a previous arrangement,
such as when a particular individual is invested in the changes being made
or a small group has worked heavily in one area.
In that case, the assignment may be more focused.

All Participants
++++++++++++++++

Try to keep all discussion contained within the pull request.
If a discussion occurs outside of the pull request comments
(e.g., video chat),
a summary of the discussion should be added
as a comment by the current assignee.

Once the pull request has been submitted,
each iteration should be completed
within one business day.
If more time is needed,
please post a comment informing all participants.

.. admonition:: Treat [Others] Like Friends and Family
   :class: note

   It is always a good reminder
   that during a pull request code review,
   it is the code being reviewed,
   not the coder.
   When leaving a comment as a part of a pull request,
   ensure that the comments address the code
   and not the coder.
   When reading a comment,
   remember that the pull review process is intended
   as a mechanism for improving the code base
   and is a mechanism for facilitating that improvement rather than speaking negatively about an individual or their abilities.

Participating As a Reviewer
+++++++++++++++++++++++++++

When starting to review a pull request,
update the **Assignees** sidebar on the *Conversation* tab
and remove any other reviewers.
The code may be reviewed either by
looking at individual commits from the *Commits* tab
or the entire code change from the *Files changed* tab.
The review process workflow
is detailed in `Reviewing proposed changes in a pull request`_.

If approving the pull request,
after clicking the *Submit review* button,
either update the **Assignees** sidebar
on the *Conversation* for the next set of reviewers or,
if the final reviewer,
merge the pull request.

If adding comments or requesting changes,
assign the pull request back to the original author.

Participating As an Author
++++++++++++++++++++++++++

When participating as an author for a code review,
if any comments are added or changes are requested,
make the necessary changes,
answer any questions,
and assign the pull request back to
the individual requesting the changes.
Note also that when the pull request checker is not sufficient (see above),
you'll need to add a link to another test run
showing that the changes made do not affect the test results.


Collaborate: Merge Pull Requests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The final reviewer,
as defined in `Collaborate: Review`_,
should merge a pull request once the pull request is approved.
If changes to the organizational repository
since the pull request was last updated
prevents the pull request from being merged cleanly,
the reviewer should assign the pull request
back to the author with a comment
explaining the need for a final update.


.. include:: ../_docs/xrefs.txt
