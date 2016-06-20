This file describes the only tags we expect to find on QE Gherkin files (ARIC and AF).
Separate tooling is used to validate that there are no other tags in use than are present here.
(Additional tags may and will be used by individual QE Devs in their own forks at will.)

The purpose column indicates why we are using the tag, and also names the group that will be used to report on that status of that tag.
At the moment, tags within any purpose are mutually exclusive.
The report as column indicates how the tag is shown when reported.

Note 1: The 'smoke' designation is used throughout Rackspace, though each team has their own interpretation of it.
Note 2: We are contemplating another status for tests taken offline so as not to disturb the component being tested while devs are working on it.

tag              | purpose     | report as   | description
---              | ---         | ---         | ---
@nyi             | status      | NYI         | Not Yet Implemented - present so we can generate reporting data on scoping.
@needs-work      | status      | Needs Work  | Test offline: problem with test that QE needs to fix.
@quarantined     | status      | Quarantined | Test offline: a bug in the application, the details are in a jira task in a test comment.
default          | status      | Operational | Default
---              | ---         | ---         | ---
@deploy          | suite       | deploy      | Build Verification Test - Must be quick. Used to validate that deploy has a pulse.
@smoke           | suite       | smoke       | Checks for basic functioning; is not an extensive test. All smoke tests should run in less than about 10 minutes.
@load            | suite       | load        | Test is designed to (help) stress/load the application. (Not a fast test.)
@solo            | suite       | solo        | Test cannot be run in parallel with any other tests.
@integration     | suite       | integration | Test exercises multiple applications not just one component.
default          | suite       | ALL         | Default
---              | ---         | ---         | ---
@production-only | environment | Production  | Can only be run in production (perhaps due to devices/accounts/systems used/needed).
@staging-only    | environment | Staging     | Can only be run in staging (perhaps due to devices/accounts/systems used/needed).
default          | environment | ALL         | Default
---              | ---         | ---         | ---
@p0              | priority    | p0          | Most important test(s) to implement first.
@p1              | priority    | p1          | Second most important test(s) to implement.
default          | priority    | p1          | Default
---              | ---         | ---         | ---
@positive        | polarity    | P           | Test is a positive/down-the-fairway case.
@negative        | polarity    | N           | Test is a negative/in-the-weeds case.
default          | polarity    | TBD         | Default
