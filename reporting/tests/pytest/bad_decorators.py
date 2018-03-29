from __future__ import print_function

import pytest


class TestCaseDecoratorsThatAreBad:
    # This will raise ValueError exception, tried wrapping with with pytest.raises
    # however because we're using hooks on test setup, wrapping the function
    # results in the tags not being parsed as part of setup
    # verify-tests.sh just ensures this bombs with a return code of 1 and
    # ValueError in the output
    @pytest.mark.tags('smoke', 'positive', 'quarantined', 'nyi')
    def test_with_conflicting_status_tags_errors_correctly(self):
        pass
