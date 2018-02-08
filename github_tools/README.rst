GitHub Tools
============

A collection of tools around Git and GitHub to make developer's lives easier.

gt-pr-checker
-------------

This PR checker is designed to signal a reviewer if a PR has not been reviewed within a given time
period. This checker works by getting the repositories associated with a provided organization and
(optionally) filtering by team name. This is done instead of providing a list of repositories to
the script because when repository is created and associated with a team, no changes would need to
be made to the arguments provided to this script.

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
