from cafe.drivers.unittest.fixtures import BaseTestFixture
from opencafe.decorators import (needs_work, not_tested, nyi, only_in,
                                 quarantined, production_only, staging_only)


class DecoratorsTestsFixture(BaseTestFixture):

    @staticmethod
    def current_environment_matches(environment):
        # For the purposes of these tests, we will say we are in a staging environment
        return environment == 'staging'


class TestCaseDecoratorsThatWork(DecoratorsTestsFixture):

    @quarantined('JIRA-111')
    def test_that_correctly_decorated_with_quarantined(self):
        self.fail('This test should have been skipped!')

    @needs_work('JIRA-222')
    def test_that_correctly_decorated_with_needs_work(self):
        self.fail('This test should have been skipped!')

    @not_tested('JIRA-333')
    def test_that_correctly_decorated_with_not_tested(self):
        self.fail('This test should have been skipped!')

    @nyi('JIRA-444')
    def test_that_correctly_decorated_with_nyi(self):
        self.fail('This test should have been skipped!')

    @only_in('staging')
    def test_that_is_decorated_with_only_in_staging_and_should_not_be_skipped(self):
        # TODO - this test will give a false positive if the test is skipped
        pass

    @only_in('production')
    def test_that_is_decorated_with_only_in_production_and_should_be_skipped(self):
        self.fail('This test should have been skipped!')

    @staging_only()
    def test_that_is_decorated_with_staging_only_and_should_not_be_skipped(self):
        # TODO - this test will give a false positive if the test is skipped
        pass

    @production_only()
    def test_that_is_decorated_with_production_only_and_should_be_skipped(self):
        self.fail('This test should have been skipped!')


@quarantined('JIRA-111')
class TestClassDecoratedAsQuarantined(DecoratorsTestsFixture):

    def test_that_should_be_skipped(self):
        self.fail('This test should have been skipped!')


@needs_work('JIRA-222')
class TestClassDecoratedAsNeedsWork(DecoratorsTestsFixture):

    def test_that_should_be_skipped(self):
        self.fail('This test should have been skipped!')


@not_tested('JIRA-333')
class TestClassDecoratedAsNotTested(DecoratorsTestsFixture):

    def test_that_should_be_skipped(self):
        self.fail('This test should have been skipped!')


@nyi('JIRA-444')
class TestClassDecoratedAsNotYetImplemented(DecoratorsTestsFixture):

    def test_that_should_be_skipped(self):
        self.fail('This test should have been skipped!')


@only_in('staging')
class TestClassDecoratedAsOnlyInStaging(DecoratorsTestsFixture):

    def test_that_should_not_be_skipped(self):
        # TODO - this test will give a false positive if the test is skipped
        pass


@only_in('production')
class TestClassDecoratedAsOnlyInProduction(DecoratorsTestsFixture):

    def test_that_should_be_skipped(self):
        self.fail('This test should have been skipped!')


@staging_only
class TestClassDecoratedAsStagingOnly(DecoratorsTestsFixture):

    def test_that_should_not_be_skipped(self):
        # TODO - this test will give a false positive if the test is skipped
        pass


@production_only
class TestClassDecoratedAsProductionOnly(DecoratorsTestsFixture):

    def test_that_should_be_skipped(self):
        self.fail('This test should have been skipped!')
