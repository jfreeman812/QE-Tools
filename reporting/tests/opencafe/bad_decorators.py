from cafe.drivers.unittest.fixtures import BaseTestFixture

from qe_coverage.opencafe_decorators import (needs_work, not_tested, nyi, only_in,
                                             quarantined, production_only, staging_only,
                                             tags)


try:
    # First decorate a test incorrectly
    class TestCaseDecoratorsThatAreBad(BaseTestFixture):

        @tags('smoke', 'positive', 'quarantined', 'nyi')
        def test_with_conflicting_status_tags_errors_correctly(self):
            pass
except ValueError as e:
    # See that the correct ValueError occurred
    class TestCaseDecoratorsThatAreBad(BaseTestFixture):

        def test_with_conflicting_status_tags_errors_correctly(self):
            # This line has the 'noqa' because of some flake8 strangeness causing an error
            # F821 undefined name 'e'
            assert str(e) == 'Conflicting Status tags, only one permitted: nyi, quarantined'  # noqa
else:
    # If no ValueError occurred, then fail the test
    class TestCaseDecoratorsThatAreBad(BaseTestFixture):

        def test_with_conflicting_status_tags_errors_correctly(self):
            raise AssertionError('This test should have raised a ValueError due to '
                                 'conflicting status tags. Please investigate.')
