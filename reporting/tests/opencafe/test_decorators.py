from cafe.drivers.unittest.datasets import DatasetList
from cafe.drivers.unittest.decorators import DataDrivenClass, DataDrivenFixture, data_driven_test
from cafe.drivers.unittest.fixtures import BaseTestFixture

from qe_coverage.opencafe_decorators import (needs_work, not_tested, nyi, only_in,
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
        return environment.lower() == 'staging'


@DataDrivenFixture
class TestDataDrivenMethods(BaseTestFixture):

    @tags('regression', 'positive')
    @data_driven_test(ItemList(range(3)))
    def ddtest_ok_data_driven_test(self, item):
        '''DataDriven test method'''


@DataDrivenClass(ItemList(range(3)))
class TestDataDrivenClass(BaseTestFixture):

    @tags('smoke', 'negative')
    def test_ok_in_data_driven_class(self):
        '''Nothing much to see here...'''

    @tags('smoke', 'positive')
    @data_driven_test(ItemList(range(3)))
    def ddtest_ok_data_driven_test_in_data_driven_class(self, item):
        '''Nothing much to see here either...'''


class TestCaseDecoratorsThatWork(DecoratorsTestsFixture):

    @tags('smoke', 'positive')
    @quarantined('JIRA-111')
    def test_skipped_quarantined(self):
        self.fail('This test should have been skipped!')

    @tags('smoke', 'positive', 'quarantined', 'JIRA-111')
    def test_ok_quarantined_but_runnable(self):
        # This test may be run as part of a special quarantined-tests run
        # to check out if a fix was successful, so it is not a failure
        # if the test is actually selected to be run.
        pass

    @quarantined('JIRA-111', environment_affected='staging')
    def test_skipped_quarantined_in_staging(self):
        self.fail('This test should have been skipped!')

    @quarantined('JIRA-111', environment_affected='production')
    def test_ok_quarantined_in_production(self):
        pass

    @tags('regression', 'negative')
    @needs_work('JIRA-222')
    def test_skipped_needs_work(self):
        self.fail('This test should have been skipped!')

    @tags('regression', 'positive')
    @not_tested('JIRA-333')
    def test_skipped_not_tested(self):
        self.fail('This test should have been skipped!')

    @tags('smoke', 'p0', 'negative')
    @nyi('JIRA-444')
    def test_skipped_nyi(self):
        self.fail('This test should have been skipped!')

    @tags('deploy', 'negative')
    @only_in('staging')
    def test_ok_only_in_staging(self):
        pass

    @tags('integration', 'positive')
    @only_in('production')
    def test_skipped_only_in_production(self):
        self.fail('This test should have been skipped!')

    @tags('load', 'positive', 'p0')
    @staging_only()
    def test_ok_staging_only(self):
        pass

    @tags('security', 'p0', 'positive')
    @production_only()
    def test_skipped_production_only(self):
        self.fail('This test should have been skipped!')

    @tags('positive')
    @quarantined('This description contains JIRA-123, but there is a comma next to it.')
    def test_skipped_quarantined_with_comma_next_to_jira_id(self):
        self.fail('This test should have been skipped!')


@quarantined('JIRA-111')
class TestClassDecoratedAsQuarantined(DecoratorsTestsFixture):

    def test_skipped_class_quarantined(self):
        self.fail('This test should have been skipped!')


@needs_work('JIRA-222')
class TestClassDecoratedAsNeedsWork(DecoratorsTestsFixture):

    def test_skipped_class_needs_work(self):
        self.fail('This test should have been skipped!')


@not_tested('JIRA-333')
class TestClassDecoratedAsNotTested(DecoratorsTestsFixture):

    def test_skipped_class_not_tested(self):
        self.fail('This test should have been skipped!')


@nyi('JIRA-444')
class TestClassDecoratedAsNotYetImplemented(DecoratorsTestsFixture):

    def test_skipped_class_nyi(self):
        self.fail('This test should have been skipped!')


@only_in('staging')
class TestClassDecoratedAsOnlyInStaging(DecoratorsTestsFixture):

    def test_ok_class_only_in_staging(self):
        pass


@only_in('production')
class TestClassDecoratedAsOnlyInProduction(DecoratorsTestsFixture):

    def test_skipped_class_only_in_production(self):
        self.fail('This test should have been skipped!')


@staging_only
class TestClassDecoratedAsStagingOnly(DecoratorsTestsFixture):

    def test_ok_class_staging_only(self):
        pass


@production_only
class TestClassDecoratedAsProductionOnly(DecoratorsTestsFixture):

    def test_skipped_class_production_only(self):
        self.fail('This test should have been skipped!')
