from __future__ import print_function

import pytest

from qe_coverage.base import run_reports, TestGroup, \
    TICKET_RE, HIERARCHY_FORMAT

# Status tags list from unittest_decorators.py
# used to verify not more than one used within tags
# see warning in unittest_decorators about this being pulled from
# coverage.rst rather than set in class files.
STATUS_TAGS = set('nyi not-tested needs-work quarantined'.split())

# Global variables used in hooks
markers = []
options = {}
test_group = TestGroup()


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
    group.addoption('--environment', default='staging',
                    help='Environment run')
    group.addoption('--no-report', action='store_true',
                    help='Run tag functions but do not compile tags')
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
    options['default-interface-type'] = config.getoption('--default-interface-type')
    options['product-hierarchy'] = config.getoption('--product-hierarchy')
    options['environment'] = config.getoption('--environment')
    options['qe-coverage'] = config.getoption('--qe-coverage')
    options['dry-run'] = config.getoption('--dry-run')
    options['preserve-files'] = config.getoption('--preserve-files')
    options['no-report'] = config.getoption('--no-report')
    options['production-endpoint'] = config.getoption('--production-endpoint')

    # Set up our global markers as this is going to be used in
    # during the run_test
    global markers
    # These are our possible tags, map to functions
    markers = [
        needs_work,
        not_tested,
        nyi,
        only_in,
        production_only,
        quarantined,
        staging_only,
        tags,
    ]

    # Use the name and first line of docstring to fill out
    # ini values that allows `pytest --markers` to work
    for marker in markers:
        name = marker.__name__
        docstr = marker.__doc__.split('\n')[1]
        docstr = docstr.strip()
        config.addinivalue_line('markers', '{}: {}'.format(name, docstr))


def pytest_runtest_setup(item):
    '''
    Hook object called before each test setup

    :param item: pytest.item object represesenting test to be run
    '''

    # Only run through our tags if `--qe-coverage` was passed
    if not _get_global_option('qe-coverage'):
        return

    _tags = []

    # Iterate through tag list and pull any pytest.mark.* tags added for qe_coverage
    for marker in markers:
        if item.get_marker(marker.__name__) is not None:
            # have a qe_coverage marker, get the tag_data from it
            # returns markinfo object of (name, *args, **kwargs)
            tag_data = item.get_marker(marker.__name__)
            # run function for marker
            # get tag_list, skip_test, skip_reason from running tag
            # used to compile tags, skip is done after compilation of
            # tag lists
            _tag_list = marker(*tag_data.args, **tag_data.kwargs)
            # add pulled tags from our tag list
            _tags.extend(_tag_list)

    # item.location is (file_path, line, testclass.testname)
    test_class = _transform_class_name_to_pretty_category(item.location[2])
    test_name = item.name

    # add information to global test_group object that on completion of tests
    # will run report
    global test_group
    test_group.add(name=test_name, categories=[test_class, test_name], tags=_tags)
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
        'production-endpoint': _get_global_option('production-endpoint'),
    }

    global test_group
    if not _get_global_option('no-report'):
        run_reports(test_group, _get_global_option('product-hierarchy'),
                    _get_global_option('default-interface-type'), **kwargs)


def _get_global_option(_option=None):
    '''
    Retreives value from global option dict

    global option dict created during pytest configuration for values of interest to
    qe_coverage and used across hooks which do not provide pytest.item objects which
    would otherwise be used to access the .config.
    :param _option:
    :return:
    '''
    global options
    return options.get(_option)


def _get_info_from_skip_type_decorator(reason, details, tag_name,
                                       environment_affected=None):
    '''
    Helper method to handle similar methods

    :param reason: Reason why test should not be run
    :param details: details in why test should not be run, requires Ticket-Ids
    :param tag_name: Name of tag calling this function
    :param environment_affected: environment in which test should be skipped
    :return: list([name,ticket-ids,])
    '''

    # Get list of ticket IDs included in details
    ticket_ids = TICKET_RE.findall(details)

    if not ticket_ids:
        raise ValueError('"{}" does not contain any Ticket IDs'.format(details))

    # Parse tickets for return
    _tags = [tag_name] + ticket_ids

    return _tags


def _transform_class_name_to_pretty_category(class_and_method_name):
    '''
    Pretty up class name for better display in Splunk

    :param class_and_method_name: str of format "className.test_method"
    :return: prettied string of "Class Name"
    '''
    class_name = class_and_method_name.split('.')[0]
    # remove /[Tt]est/ if it is there
    if class_name.lower().startswith('test'):
        class_name = class_name[4:]

    breakpoints = _get_breakpoints(class_name)
    name_as_list = break_string(class_name, breakpoints)
    list_as_string = ' '.join(name_as_list)
    return list_as_string.strip()


def _get_breakpoints(camel_case_string):
    '''
    Helper method for _transform_class_name_to_pretty_category

    Creates a list of breakpoints of capital letters to split string

    :param camel_case_string: str of format(TestClassName) to be split
    :return: list of breakpoints
    '''
    tmp_list = [i for i, c in enumerate(camel_case_string) if c.isupper()]
    tmp_list.append(len(camel_case_string))
    return tmp_list


def break_string(input_string, breakpoints):
    '''
    Helper method for _transform_class_name_to_pretty_category

    Creates list of words split on list of indexes of capital letters

    :param input_string: string of camel cased word
    :param breakpoints: list of indexes of capital letters in word (from _get_breakpoints)
    :return:
    '''
    substrings = []
    for x in range(0, len(breakpoints) - 1):
        substrings.append(input_string[breakpoints[x]:breakpoints[x + 1]])
    return substrings


def _raise_value_error_if_conflicting_status_tags(tag_list):
    '''
    Verify single status tag used.

    Args:
        tag_list (iterable of str): The list of tags.

    Raises:
        ValueError if more than one Status tag has been used.
    '''

    actual_status_tags = set(tag_list) & STATUS_TAGS

    if len(actual_status_tags) > 1:
        overlapping_tags = sorted(actual_status_tags)
        msg = 'Conflicting Status tags, only one permitted: {}'.format(', '.join(overlapping_tags))
        raise ValueError(msg)


def only_in(*args, **kwargs):
    '''
    Mark as only in specific environment, skip if not that environment

    Used to run a test only during a specific environment run. Environment run specified
    via the ``--environment`` argument when running pytest

    Args:
        environment (str): Environment test can only run in
        reason (str): reason test can only be run in specified environment.

    Returns:
        str(reason)
    '''
    reason = 'Only tested in {}'.format(args[0])

    # Allow reason in either args or kwargs
    if len(args) > 1:
        reason += ': {}'.format(args[1])
    elif kwargs.get('reason', None) is not None:
        reason += ': {}'.format(kwargs.get('reason'))

    return reason


def production_only(*args, **kwargs):
    '''
    Mark as production only and skip if not running as production

    Used to run a test only during a Production environment run. Environment run specified
    via the ``--environment`` argument when running pytest

    Args:
        reason (str): Information on why test only runs in production

    Returns:
        str(reason)
    '''
    return only_in('production', *args, **kwargs)


def staging_only(*args, **kwargs):
    '''
    Marked as staging only and skip if not in staging environment

    Used to run a test only during a Staging environment run. Environment run specified
    via the ``--environment`` argument when running pytest

    Args:
        reason (str): Information about why test only runs in staging.

    Returns:
        A tuple of ( list[tags from details], bool(skip reason), str(skip message from details)
    '''
    return only_in('staging', *args, **kwargs)


def quarantined(*args, **kwargs):
    '''
    Mark as quarantined and skip the test

    This should be used for test cases that are not functioning properly due to an issue
    with the system being tested that is outside the scope of the QE team.

    The ``details`` parameter should include the ID for the ticket.
    If no ID exists, a ticket should be created before marking the test as
    needs work.

    Args:
        details (str): Information about why the test is quarantined
        environment_affected (str): The only environment in which the decorator applies.

    Returns:
        A tuple of ( list[tags from details], bool(skip reason), str(skip message from details)
    '''
    env_affected = kwargs.get('environment_affected')
    return _get_info_from_skip_type_decorator(reason='Quarantined', details=' '.join(list(args)),
                                              tag_name='quarantined',
                                              environment_affected=env_affected)


def needs_work(*args, **kwargs):
    '''
    Mark as needs_work and skip the test case

    This should be used for test cases that are not functioning properly due to an
    issue with the test or test framework. This issue should be something that will
    be fixed by the QE team.

    The ``details`` parameter should include the ID for the ticket.
    If no ID exists, a ticket should be created before marking the test as
    needs work.

    Args:
        details (str): Information about why the test needs work

    Returns:
        A tuple of ( list[tags from details], bool(skip reason), str(skip message from details)
    '''
    return _get_info_from_skip_type_decorator(reason='Needs Work', details=' '.join(args),
                                              tag_name='needs_work')


def not_tested(*args, **kwargs):
    '''
    Mark as not tested and skip the test

    This should be used for test cases that are implemented, but the service being
    tested is not ready..

    The ``details`` parameter should include the ID for the ticket.
    If no ID exists, a ticket should be created before marking the test as
    needs work.

    Args:
        details (str): Information about why the test is not tested.

    Returns:
        A tuple of ( list[tags from details], bool(skip reason), str(skip message from details)
    '''
    return _get_info_from_skip_type_decorator(reason='Not Tested', details=' '.join(args),
                                              tag_name='not_tested')


def nyi(*args, **kwargs):
    '''
    Mark as not yet implemented and skip the test

    This should be used for test cases that have a method definition but
    are not yet implemented.

    The ``details`` parameter should include the ID for the ticket.
    If no ID exists, a ticket should be created before marking the test as
    needs work.

    Args:
        details (str): Typically just ticket ID but other information can be included.

    Returns:
        A tuple of ( list[tags from details], bool(skip reason), str(skip message from details)
    '''
    return _get_info_from_skip_type_decorator(reason='Not Yet Implemented', details=' '.join(args),
                                              tag_name='nyi')


def tags(*args, **kwargs):
    '''
    Used primarily for non status specific tags such as suite, polarity, or priority.

    Args:
        tag_list (list): List of relevant tags

    Returns:
        A tuple of ( list[tags from details], bool(skip reason), str(skip message from details)
    '''
    _raise_value_error_if_conflicting_status_tags(list(args))
    return list(args)
