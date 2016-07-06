This file describes the only tags we expect to find on QE Gherkin files (ARIC and AF).
Additional tags may and will be used by individual QE Devs in their own repos, however,
only the tags listed here should be accepted into a master/"blessed" group repo.

The 'purpose' column indicates why we are using the tag, and is also the name of the reporting group for that tag.
At the moment, tags with the same purpose are mutually exclusive.
The 'report as' column indicates how the tag is shown when reported.

Note: The 'smoke' designation is used throughout Rackspace, though each team has their own interpretation of it.

tag              | purpose     | report as   | description
-----------      | ----------- | ----------- | -----------
@nyi             | status      | NYI         | Not Yet Implemented - test is a skeleton for generating data on scoping.
@not-tested      | status      | Not Tested  | Test is ready, but the service / subject is not ready
@needs-work      | status      | Needs Work  | Test offline; problem with test; QE needs to fix (JIRA ID in comments).
@quarantined     | status      | Quarantined | Test offline; bug in application/system/etc. outside QE's scope to fix. (JIRA ID in comments).
                 | status      | Operational | *Default when no tag for this purpose is used.*
-----------      | ----------- | ----------- | -----------
@deploy          | suite       | Deploy      | Build Verification Test Quick test to validate successful deployment, does not test system functionality.
@smoke           | suite       | Smoke       | Checks for basic functioning; is not an extensive test. All smoke tests should run in less than about 10 minutes.
@load            | suite       | Load        | Test is designed to (help) stress/load the application. (Not a fast test.)
@solo            | suite       | Solo        | Test cannot be run in parallel with any other tests.
@integration     | suite       | Integration | Test exercises multiple applications not just one component.
                 | suite       | ALL         | *Default when no tag for this purpose is used.*
-----------      | ----------- | ----------- | -----------
@production-only | environment | Production  | Can only be run in production (perhaps due to devices/accounts/systems used/needed).
@staging-only    | environment | Staging     | Can only be run in staging (perhaps due to devices/accounts/systems used/needed).
                 | environment | ALL         | *Default when no tag for this purpose is used.*
-----------      | ----------- | ----------- | -----------
@p0              | priority    | p0          | Most important test(s) to implement first.
@p1              | priority    | p1          | Second most important test(s) to implement.
                 | priority    | p1          | *Default when no tag for this purpose is used.*
-----------      | ----------- | ----------- | -----------
@positive        | polarity    | Positive    | Test is a positive/down-the-fairway case.
@negative        | polarity    | Negative    | Test is a negative/in-the-weeds case.
                 | polarity    | TBD         | *Default when no tag for this purpose is used.*
