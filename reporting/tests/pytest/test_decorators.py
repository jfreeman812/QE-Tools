from __future__ import print_function
import pytest


@pytest.fixture()
def decoratorsTestsFixture(staging_env):
    return ''

class TestCaseDecoratorsThatWork:

    @pytest.mark.quarantined('JIRA-1234')
    @pytest.mark.tags('positive', 'smoke', 'quarantined', 'JIRA-111')
    def test_skipped_quarantined(self, decoratorsTestsFixture):
        print('This test should have been skipped')
        assert False

    @pytest.mark.tags('smoke', 'positive', 'quarantined', 'JIRA-111')
    def test_ok_quarantined_but_runnable(self):
        # This test may be run as part of a special quarantined-tests run
        # to check out if a fix was successful, so it is not a failure
        # if the test is actually selected to be run.
        pass

    @pytest.mark.quarantined('JIRA-111', environment_affected='staging')
    def test_skipped_quarantined_in_staging(self):
        print('This test should have been skipped!')
        assert False

    @pytest.mark.quarantined('JIRA-111', 'JIRA-123', environment_affected='production')
    def test_ok_quarantined_in_production(self):
        pass

    @pytest.mark.tags('regression', 'negative')
    @pytest.mark.needs_work('JIRA-222')
    def test_skipped_needs_work(self):
        print('This test should have been skipped!')
        assert False

    @pytest.mark.tags('regression', 'positive')
    @pytest.mark.not_tested('JIRA-333')
    def test_skipped_not_tested(self):
        print('This test should have been skipped!')
        assert False

    @pytest.mark.tags('smoke', 'p0', 'negative')
    @pytest.mark.nyi('JIRA-444')
    def test_skipped_nyi(self):
        print('This test should have been skipped!')
        assert False

    @pytest.mark.tags('deploy', 'negative')
    @pytest.mark.only_in('staging')
    def test_ok_only_in_staging(self):
        pass

    @pytest.mark.tags('integration', 'positive')
    @pytest.mark.only_in('production')
    def test_skipped_only_in_production(self):
        print('This test should have been skipped!')
        assert False

    @pytest.mark.tags('load', 'positive', 'p0')
    @pytest.mark.staging_only()
    def test_ok_staging_only(self):
        pass

    @pytest.mark.tags('security', 'p0', 'positive')
    @pytest.mark.production_only()
    def test_skipped_production_only(self):
        print('This test should have been skipped!')
        assert False

    @pytest.mark.tags('positive')
    @pytest.mark.quarantined('This description contains JIRA-123, but there is a comma next to it.')
    def test_skipped_quarantined_with_comma_next_to_jira_id(self):
        print('This test should have been skipped!')
        assert False


@pytest.mark.quarantined('JIRA-111')
class TestClassDecoratedAsQuarantined:

    def test_skipped_class_quarantined(self):
        print('This test should have been skipped!')
        assert False


@pytest.mark.needs_work('JIRA-222')
class TestClassDecoratedAsNeedsWork:

    def test_skipped_class_needs_work(self):
        print('This test should have been skipped!')
        assert False


@pytest.mark.not_tested('JIRA-333')
class TestClassDecoratedAsNotTested:

    def test_skipped_class_not_tested(self):
        print('This test should have been skipped!')
        assert False


@pytest.mark.nyi('JIRA-444')
class TestClassDecoratedAsNotYetImplemented:

    def test_skipped_class_nyi(self):
        print('This test should have been skipped!')
        assert False


@pytest.mark.only_in('staging')
class TestClassDecoratedAsOnlyInStaging:

    def test_ok_class_only_in_staging(self):
        pass


@pytest.mark.only_in('production', reason="due to breakage")
class TestClassDecoratedAsOnlyInProduction:

    def test_skipped_class_only_in_production(self):
        print('This test should have been skipped!')
        assert False

@pytest.mark.staging_only
class TestClassDecoratedAsStagingOnly:

    def test_ok_class_staging_only(self):
        pass


@pytest.mark.production_only
class TestClassDecoratedAsProductionOnly:

    def test_skipped_class_production_only(self):
        print('This test should have been skipped!')
        assert False

