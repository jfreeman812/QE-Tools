GitHub Tools
============

A collection of tools around Git and GitHub to make developers' lives easier.

- `gt-pr-checker`_
- `gt-install-hooks`_

gt-pr-checker
-------------

This PR checker is designed to signal a reviewer if a PR has not been reviewed within a given time
period. This checker works by getting the repositories associated with a provided organization and
(optionally) filtering by team name. This is done instead of providing a list of repositories to
the script because when a repository is created and associated with a team, no changes would need
to be made to the arguments provided to this script.

Usage
~~~~~

The tool requires a token and organization. The token comes from a user (service account or real)
and can be obtained by navigating from https://github.rackspace.com to User -> Settings and
selecting **Personal access tokens**. The organization is *just* the organization name (not the
full GitHub URL for the organization)

The default time period is 20 hours, but can be modified using the ``--pr-age`` option. The value
is in **seconds**. By default, all Pull Requests within a GitHub organization are checked. However,
the ``--name-filter`` option checks for any repositories affiliated with the team(s) that start
with the string provided. For example, if there are multiple GitHub teams affiliated with a QE
team (e.g., ``qe-tools-api`` and ``qe-tools-ui``), then ``--name-filter`` could be called with
``qe-tools`` and all repositories associated with both GitHub teams will be checked, but no other
repositories.

gt-install-hooks
----------------

Install useful git hooks that work within common workflows. These hooks may be installed separately from this script, but this script provides an easy mechanism for installing and updating them in existing repositories.

commit-msg
~~~~~~~~~~

Ensure that a commit message conforms to some best practices:

#. Subject lines should not be longer than 50 characters
#. Wrap the body at 72 characters
#. Separate the subject from body with a blank line.

These are taken from `A Note About Git Commit Messages`_.

pre-commit
~~~~~~~~~~

Can perform validations before making a commit. If an executable file named ``self-check.sh`` exists in the root of the repository and a Python, Ruby, or Gherkin file was changed, the checker is executed and the return status serves as a gate for the commit to occur. The check can be bypassed via ``git commit -n``.

prepare-commit-msg
~~~~~~~~~~~~~~~~~~

Prepare a commit message by including an appropriate prefix, when possible, based on the branch name. If the branch name contains a JIRA ID, that is included in the prefix. If the branch name also contains either "FF" or "Spike", that is appended to the prefix. If a branch name, without including a JIRA ID, contains "FF", "Spike", "Enhancement" or "Fix", those phrases are set as the prefix. All searches are case-insensitive.

.. include:: ../xrefs.txt
