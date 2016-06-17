This file describes the only tags we expect to find on QE Gherkin files (ARIC and AF).
Separate tooling is used to validate that there are no other tags in use than are present here.

tag             | tag purpose      | description
---             | ---              | ---
nyi             | test code status | Not Yet Implemented - Could even be just a skeleton, but is present so we can generate reporting data.
needs-work      | test code status | Work In Progress - test hasn't been validated yet, probably because the service is failing or not implemented
skip            | test code status | this test is offline awaiting maintenance, it will still be run but will be reported as a qurantined failure or passed
quarantined     | test code status | this test has been quarantined because of the jira task in the comment
deploy          | test scope       | Build Verification Test - test checks that the system is running. Must be quick. Used to validate a build/deploy has a pulse and that is all.
smoke           | test scope       | Checks that a component is basically functioning. Cannot take too long, and is not an extensive test. This term is used throughout Rackspace though each QE team has their own definition (attempts to unify that definition have been unsuccessful to date). All the smoke tests should run in less than about 10 minutes.
load            | test scope       | test is designed to (help) stress/load the system. Not a fast test.
solo            | test scope       | test cannot be run in parallel with any other tests
end-2-end       | test scope       | indicates this test will test the entire system e.g. for RBA this would be a process test
production-only | environment      | can only be run in production (perhaps due to devices/accounts/systems used/needed)
staging-only    | environment      | can only be run in staging (perhaps due to devices/accounts/systems used/needed)
mvp             | reporting        | most important test(s) to implement first.
negative        | reporting        | test is a negative/in-the-weeds case
repeat          | reporting        | this test is a repeat of another test
sparadic        | reporting        | this test is known to be unstable so a signle pass does not mean the problem is fixed
