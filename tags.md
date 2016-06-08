This file describes the only tags we expect to find on QE Gherkin files (ARIC and AF).
Separate tooling is used to validate that there are no other tags in use than are present here.

tag             | tag purpose      | Description
---             | ---              | ---
nyi             | test code status | test is defined but not yet implemented. Could even be just a skeleton
needs-work      | test code status | test used to work but something changed and it is offline awaiting maintenance
bvt             | test scope       | Build Verification Test - test checks that the system is running. Must be quick. Used to validate a build/deploy has a pulse and that is all.
smoke           | test scope       | Checks that a component is basically functioning. Cannot take too long, and is not an extensive test. This term is used throughout Rackspace though each QE team has their own definition (attempts to unify that definition have been unsuccessful to date). All the smoke tests should run in less than about 10 minutes.
load            | test scope       | test is designed to (help) stress/load the system. Not a fast test.
destructive     | test scope       | Ben's suggestion. Needs clarification, does a test which creates something and then deletes it count?
solo            | test scope       | test cannot be run in parallel with any other tests
production-only | environment      | can only be run in production (perhaps due to devices/accounts/systems used/needed)
staging-only    | environment      | can only be run in staging (perhaps due to devices/accounts/systems used/needed)
nyi             | reporting        | test is defined but not yet implemented. Could even be just a skeleton, but is present so we can generate reporting data.
mvp             | reporting        | most important test(s) to implement first.
positive        | reporting        | test is a positive/fairway case
negative        | reporting        | test is a negative/in-the-weeds case
