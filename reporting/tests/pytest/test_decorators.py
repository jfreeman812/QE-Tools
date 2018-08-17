from __future__ import print_function

import pytest


class TestCaseDecoratorsThatWork:

    @pytest.mark.tags('positive', 'smoke', 'quarantined', 'JIRA-111')
    def test_succeeds_with_tags(self):
        assert True

    @pytest.mark.tags('positive', 'smoke', 'unstable', 'JIRA-123')
    def test_succeeds_with_unstable_tag(self):
        assert True

    @pytest.mark.tags('smoke', 'positive', 'quarantined', 'JIRA-111', 'JIRA-1234')
    def test_passes_with_multiple_tickets(self):
        # This test may be run as part of a special quarantined-tests run
        # to check out if a fix was successful, so it is not a failure
        # if the test is actually selected to be run.
        assert True

    @pytest.mark.tags('regression', 'negative', 'JIRA-1234', 'nyi', 'JIRA-2345')
    def test_passes_with_ticket_implementation_and_status(self):
        assert True

    @pytest.mark.tags('smoke', 'JIRA-4321', 'positive', 'quarantined', 'JIRA-111', 'JIRA-1234')
    def test_passes_with_multiple_ticket_before_and_after_status(self):
        # This test may be run as part of a special quarantined-tests run
        # to check out if a fix was successful, so it is not a failure
        # if the test is actually selected to be run.
        assert True
