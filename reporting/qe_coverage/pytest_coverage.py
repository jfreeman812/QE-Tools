from __future__ import print_function

import pytest

from qe_coverage.base import run_reports, TestGroup, HIERARCHY_FORMAT

# Global variables used in hooks
options = {}
test_group = TestGroup('pytest')


def pytest_addoption(parser):
    '''
    Hook object run on pytest run

    :param parser: pytest parser object
    '''
    group = parser.getgroup('qe_coverage')
    group.addoption('--qe-coverage', action='store_true',
                    help='Run QE-Tools qe_coverage')
    group.addoption('--default-interface-type', choices='gui api'.split(),
                    help='The interface type of the product if it is not otherwise specified')
    group.addoption('--product-hierarchy',
                    help='Product hierarchy, formatted {}'.format(HIERARCHY_FORMAT))
    group.addoption('--dry-run', action='store_true',
                    help='Run qe_coverage, do not report')
    group.addoption('--preserve-files', action='store_true',
                    help='Preserve report files generated')
    group.addoption('--production-endpoint', action='store_true',
                    help='Send coverage data to the production endpoint')


def pytest_configure(config):
    '''
    Hook object run on pytest initial configuration

    :param config: Pytest config object
    '''
    # Get our options needed for the coverage schema
    # Not all of our hooks will pass objects that can get these options,
    # so we're updating our object here, and will grab them with the
    # _get_global_option function
    global options
    options['qe-coverage'] = config.getoption('--qe-coverage')
    options['default-interface-type'] = config.getoption('--default-interface-type')
    options['product-hierarchy'] = config.getoption('--product-hierarchy')
    options['dry-run'] = config.getoption('--dry-run')
    options['preserve-files'] = config.getoption('--preserve-files')
    options['production-endpoint'] = config.getoption('--production-endpoint')

    # Add our @pytest.mark.tags info to be displayed with `pytest --markers`
    tag_marker_info = 'tags: List of qe_coverage tags to report in coverage_metrics schema'
    config.addinivalue_line('markers', tag_marker_info)


def pytest_runtest_setup(item):
    '''
    Hook object called before each test setup

    :param item: pytest.item object represesenting test to be run
    '''

    # Do nothing special if we're not running coverage
    if not _get_global_option('qe-coverage'):
        return

    # look for @pytest.marker.tags and @pytest.marker.categories
    _tags = item.get_closest_marker('tags')
    _categories = item.get_closest_marker('categories')

    # bail if there isn't a tags marker
    if _tags is None:
        error_message = 'qe_coverage run but test "{}" not marked with have @pytest.mark.tags()'
        raise NotImplementedError(error_message.format(item.location[2]))

    # get args in @pytest.mark.tags, cast to list from tuple
    _tags = list(_tags.args)

    # item.location is (file_path, line, testclass.testname)
    test_class = _transform_class_name_to_pretty_category(item.location[2])
    test_name = item.name

    # get args in @pytest.mark.categories
    _categories = list(_categories.args) if _categories else [test_class]
    _categories.append(test_name)

    # add information to global test_group object that on completion of tests
    # will run report
    global test_group
    test_group.add(name=test_name, categories=_categories, tags=_tags)
    pytest.skip()


def pytest_terminal_summary(terminalreporter, exitstatus):
    '''
    Hook object called at completion of test run before displaying summary

    Used as hook as this is one of the last available hooks in pytest. Called before
    providing terminal summary, we're just using it to process the report
    :param terminalreporter: pytest terminalreporter object
    :param exitstatus: pytest exitstatus reported to system
    '''
    kwargs = {
        'dry_run': _get_global_option('dry-run') or False,
        'preserve_files': _get_global_option('preserve-files'),
        'production_endpoint': _get_global_option('production-endpoint'),
    }
    global test_group
    if _get_global_option('qe-coverage'):
        run_reports(test_group, _get_global_option('product-hierarchy'),
                    _get_global_option('default-interface-type'), **kwargs)


def _get_global_option(_option=None):
    '''
    Retreives value from global option dict

    global option dict created during pytest configuration for values of interest to
    qe_coverage and used across hooks which do not provide pytest.item objects which
    would otherwise be used to access the .config.
    Args:
        _option: str option to be returned

    Returns:
        string of found option or None
    '''
    global options
    return options.get(_option)


def _transform_class_name_to_pretty_category(class_and_method_name):
    '''
    Pretty up class name for better display in Splunk

    Args:
        class_and_method_name: str of format "className.test_method"

    Returns:
        prettied string of "Class Name"
    '''
    class_name = class_and_method_name.split('.')[0]
    # remove /[Tt]est/ if it is there
    if class_name.lower().startswith('test'):
        class_name = class_name[4:]

    breakpoints = _get_breakpoints(class_name)
    name_as_list = _break_string(class_name, breakpoints)
    list_as_string = ' '.join(name_as_list)
    return list_as_string.strip()


def _get_breakpoints(camel_case_string):
    '''
    Helper method for _transform_class_name_to_pretty_category

    Creates a list of breakpoints of capital letters to split string

    Args:
        camel_case_string: str of format(TestClassName) to be split

    Returns:
         list of breakpoints
    '''
    tmp_list = [i for i, c in enumerate(camel_case_string) if c.isupper()]
    tmp_list.append(len(camel_case_string))
    return tmp_list


def _break_string(input_string, breakpoints):
    '''
    Helper method for _transform_class_name_to_pretty_category

    Creates list of words split on list of indexes of capital letters

    Args:
        input_string: string of camel cased word
        breakpoints: list of indexes of capital letters in word (from _get_breakpoints)

    Returns:
        List of strings
    '''
    substrings = []
    for x in range(0, len(breakpoints) - 1):
        substrings.append(input_string[breakpoints[x]:breakpoints[x + 1]])
    return substrings
