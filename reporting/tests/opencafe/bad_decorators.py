from cafe.drivers.unittest.fixtures import BaseTestFixture
from qe_coverage.opencafe_decorators import (needs_work, not_tested, nyi, only_in,
                                             quarantined, production_only, staging_only,
                                             tags)


class TestCaseDecoratorsThatAreBad(BaseTestFixture):

    @tags('smoke', 'positive', 'quarantined', 'nyi')
    def test_with_conflicting_decorators(self):
        pass
