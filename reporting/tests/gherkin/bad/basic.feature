Feature: Bad Feature File

    Scenario: Untagged Test

        Given an untagged test
        When the coverage tool runs
        Then the tool completes with an error

    @p0
    Scenario: Missing Tag

        Given an test with insufficient tagging
        When the coverage tool runs
        Then the tool completes with an error

    @p0 @negative
    @quarantined
    Scenario: Missing Ticket Tag

        Given a test with a status and no ticket tag
        When the coverage tool runs
        Then the tool completes with an error

    @positive @negative
    Scenario: Multiple Prescriptive Tags

        Given a test with too many tags for a given attribute
        When the coverage tool runs
        Then the tool completes without errors

    @category:test @category:test:two
    @negative
    Scenario: Multiple Categories

        Given a test with too many categories
        When the coverage tool runs
        Then the tool completes without errors
