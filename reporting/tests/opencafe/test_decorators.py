from cafe.drivers.unittest.datasets import DatasetList
from cafe.drivers.unittest.decorators import DataDrivenClass, DataDrivenFixture, data_driven_test
from cafe.drivers.unittest.fixtures import BaseTestFixture
from opencafe_decorators import (needs_work, not_tested, nyi, only_in,
                                 quarantined, production_only, staging_only,
                                 tags)


class ItemList(DatasetList):
    '''For any datadriven test that needs a list of things/items'''
    def __init__(self, item_iterator):
        super(ItemList, self).__init__()
        for item in item_iterator:
            self.append_new_dataset(item, {'item': item})


class DecoratorsTestsFixture(BaseTestFixture):

    @staticmethod
    def current_environment_matches(environment):
        # For the purposes of these tests, we will say we are in a staging environment
        return environment == 'staging'


@DataDrivenFixture
class TestDataDrivenMethods(BaseTestFixture):

    @tags('regression', 'positive')
    @data_driven_test(ItemList(range(3)))
    def ddtest_that_is_data_driven(self, item):
        '''DataDriven test method'''


@DataDrivenClass(ItemList(range(3)))
class TestDataDrivenClass(BaseTestFixture):

    @tags('smoke', 'negative')
    def test_in_data_driven_class(self):
        '''Nothing much to see here...'''

    @tags('smoke', 'positive')
    @data_driven_test(ItemList(range(3)))
    def ddtest_data_driven_test_in_data_driven_class(self, item):
        '''Nothing much to see here either...'''


class TestCaseDecoratorsThatWork(DecoratorsTestsFixture):

    @tags('smoke', 'positive')
    @quarantined('JIRA-111')
    def test_that_correctly_decorated_with_quarantined(self):
        self.fail('This test should have been skipped!')

    @tags('smoke', 'positive', 'quarantined', 'JIRA-111')
    def test_quarantined_but_runnable(self):
        # This test may be run as part of a special quarantined-tests run
        # to check out if a fix was successful, so it is not a failure
        # if the test is actually selected to be run.
        pass

    @tags('regression', 'negative')
    @needs_work('JIRA-222')
    def test_that_correctly_decorated_with_needs_work(self):
        self.fail('This test should have been skipped!')

    @tags('regression', 'positive')
    @not_tested('JIRA-333')
    def test_that_correctly_decorated_with_not_tested(self):
        self.fail('This test should have been skipped!')

    @tags('smoke', 'p0', 'negative')
    @nyi('JIRA-444')
    def test_that_correctly_decorated_with_nyi(self):
        self.fail('This test should have been skipped!')

    @tags('deploy', 'negative')
    @only_in('staging')
    def test_that_is_decorated_with_only_in_staging_and_should_not_be_skipped(self):
        # TODO - this test will give a false positive if the test is skipped
        pass

    @tags('integration', 'positive')
    @only_in('production')
    def test_that_is_decorated_with_only_in_production_and_should_be_skipped(self):
        self.fail('This test should have been skipped!')

    @tags('load', 'positive', 'p0')
    @staging_only()
    def test_that_is_decorated_with_staging_only_and_should_not_be_skipped(self):
        # TODO - this test will give a false positive if the test is skipped
        pass

    @tags('security', 'p0', 'positive')
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
