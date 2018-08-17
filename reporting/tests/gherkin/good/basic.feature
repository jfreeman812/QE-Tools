Feature: Example of Good Gherkin

    @p0 @positive
    Scenario: Simple Happy Path

        Given a Gherkin file
        When I run the coverage tool
        Then I return without any errors

    @p0 @positive
    @quarantined @JIRA-1234
    Scenario: Quarantined Test

        Given a quarantined test
        When I run the coverage tool
        Then I return without any errors


    @p0 @positive
    @unstable @JIRA-1234
    Scenario: Unstable Test

        Given an unstable test
        When I run the coverage tool
        Then I return without any errors
