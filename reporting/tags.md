This file describes the only tags we expect to find on QE Gherkin files (ARIC and AF).
Additional tags may and will be used by individual QE Devs in their own repos, however,
only the tags listed here should be accepted into a master/"blessed" group repo.

The reason for these tags is two fold:
* to allow us to control test selection during test runs
* to generate automatic scoping / coverage reports for management

The 'purpose' column indicates why we are using the tag,
and is also the name of the group for that tag in the scoping report.
The 'report as' column indicates how the tag is shown in the scoping report.

Tags with the same purpose are mutually exclusive.
Any purpose whose name starts with a hyphen (-) is not reported on, but will
be otherwise checked.


Note: The 'smoke' designation is used throughout Rackspace, though each team has their own interpretation of it.

tag              | purpose          | report as   | description
-----------      | ---------------- | ----------- | -----------
@nyi             | status           | pending     | Not Yet Implemented - test is a skeleton for generating data on scoping.
@not-tested      | status           | pending     | Test is ready, but the service / subject is not ready
@needs-work      | status           | needs work  | Test offline; problem with test; QE needs to fix (JIRA ID in comments).
@quarantined     | status           | quarantined | Test offline; bug in application/system/etc. outside QE's scope to fix. (JIRA ID in comments).
<blank>          | status           | operational | *Default when no tag for this purpose is used.*
-----------      | ---------------- | ----------- | -----------
@deploy          | suite            | unit        | Build Verification Test Quick test to validate successful deployment, does not test system functionality.
@smoke           | suite            | unit        | Checks for basic functioning; is not an extensive test. All smoke tests should run in less than about 10 minutes.
@load            | suite            | performance | Test is designed to (help) stress/load the application. (Not a fast test.)
@solo            | suite            | solo        | Test cannot be run in parallel with any other tests.
@integration     | suite            | integration | Test exercises multiple applications not just one component.
@security        | suite            | security    | Test is a security test.
<blank>          | suite            | all         | *Default when no tag for this purpose is used.*
-----------      | ---------------- | ----------- | -----------
@production-only | -environment     | production  | Can only be run in production (perhaps due to devices/accounts/systems used/needed).
@staging-only    | -environment     | staging     | Can only be run in staging (perhaps due to devices/accounts/systems used/needed).
<blank>          | -environment     | all         | *Default when no tag for this purpose is used.*
-----------      | ---------------- | ----------- | -----------
@p0              | priority         | p0          | Most important test(s) to implement first.
@p1              | priority         | p1          | Second most important test(s) to implement.
@p2              | priority         | p2          | Third most important test(s) to implement.
<blank>          | priority         | p1          | *Default when no tag for this purpose is used.*
-----------      | ---------------- | ----------- | -----------
@positive        | polarity         | positive    | Test is a positive/down-the-fairway case.
@negative        | polarity         | negative    | Test is a negative/in-the-weeds case.
-----------      | ---------------- | ----------- | -----------
@manual          | execution        | manual      | Test description is of a manual test, present for coverage reporting.
@automated       | execution        | automated   | Test is automated.
<blank>          | execution        | automated   | *Default when no tag for this purpose is used.*
-----------      | ---------------- | ----------- | -----------
@fast            | -speed           | fast        | Test runs "fast" (within a few minutes)
@slow            | -speed           | slow        | Test runs "slow" (scenario takes > 5 minutes to run).
<blank>          | -speed           | fast        | *Default when no tag for this purpose is used.*
