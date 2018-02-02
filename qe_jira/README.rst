qe_jira
=======

A simple helper tool to create a test JIRA from a given dev JIRA

Setup
-----

* Copy jira.config.example to ~/jira.config
* Fill out the config values with your appropriate data

Usage Examples
--------------

* ``qe_jira JIRA-1234`` -- will create a JIRA in your ``TEST_PROJECT`` to test
  JIRA-1234, and link the two, assigning it to you and adding any watchers
  specified
* ``qe_jira JIRA-1234 --project OTHER`` -- will create a test JIRA as above, but in ``OTHER``
* ``qe_jira JIRA-1234 --user bobm5523`` -- will create the JIRA as above, but
  assign to ``bobm5523``
* ``qe_jira JIRA-1234 -w sall9987 -w benj4444`` -- will create the JIRA and assign
  ``sall9987`` and ``benj4444`` as watchers instead of your default watcher list
