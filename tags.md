This file describes the only tags we expect to find on QE Gherkin files (ARIC and AF).
Separate tooling is used to validate that there are no other tags in use than are present here.

The purpose column indicates why we are using the tag, and also names the group that will be
used to report on that status of that tag.  At the moment, tags within any purpose are mutually exclusive.
The report as column indicates how the tag is shown when reported.

tag              | purpose     | report as   | description
---              | ---         | ---         | ---
@nyi             | status      | NYI         | Not Yet Implemented - present so we can generate reporting data on scoping.
@needs-work      | status      | Needs Work  | Test is offline because of a test problem that needs to be fixed.
@quarantined     | status      | Quarantined | This test has been quarantined because of the jira task in the comment.
@bvt             | suite       | bvt         | Build Verification Test - Must be quick. Used to validate a build/deploy has a pulse.
@smoke           | suite       | smoke       | Checks that a component is basically functioning. Cannot take too long, and is not an extensive test. This term is used throughout Rackspace though each QE team has their own definition (attempts to unify that definition have been unsuccessful to date). All the smoke tests should run in less than about 10 minutes.
@load            | suite       | load        | Test is designed to (help) stress/load the system. Not a fast test.
@solo            | suite       | solo        | Test cannot be run in parallel with any other tests
@production-only | environment | Production  | Can only be run in production (perhaps due to devices/accounts/systems used/needed)
@staging-only    | environment | Staging     | Can only be run in staging (perhaps due to devices/accounts/systems used/needed)
@p0              | priority    | p0          | Most important test(s) to implement first.
@p1              | priority    | p1          | Second most important test(s) to implement.
@positive        | polarity    | P           | Test is a positive/down-the-fairway case
@negative        | polarity    | N           | Test is a negative/in-the-weeds case
