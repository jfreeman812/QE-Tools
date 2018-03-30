from __future__ import print_function

import pytest


class TestCaseDecoratorsThatAreBad:
    # This will raise ValueError exception, tried wrapping with with pytest.raises
    # however because we're using hooks on test setup, wrapping the function
    # results in the tags not being parsed as part of setup
    # verify-tests.sh just ensures this bombs with a return code of 1 and
    # ValueError in the output
    @pytest.mark.tags('smoke', 'positive', 'quarantined', 'nyi', 'JIRA-1234')
    def test_with_conflicting_status_tags_errors_correctly(self):
        pass

    @pytest.mark.tags('smoke', 'positive', 'integration', 'security')
    def test_with_conflicting_suite_tags_reports_error_in_testgroup(self):
        pass

    @pytest.mark.tags('smoke', 'positive', 'integration', 'nyi')
    def test_with_status_tag_requires_ticket_id(self):
        pass

    def test_with_no_tags_throws_error(self):
        pass
