'''
Common decorators for decorating OpenCafe test fixtures and test methods.


**Skipping Tests**

A number of these decorators are designed to utilize the ``unittest.skip``
decorator, or the the ``SkipTest`` exception, both of which skip a test
method or test class for a specific reason.


**Docstring Hacking**

By default, these decorators manipulate the original docstring of the
decorated test class to include additional information in the summary
line.

This is designed to include the current state of a test in the test
documentation autogenerated by Sphinx.

For example, if a test is decorated like so::

    @quarantined('JIRA-123')
    def example_test(self):
        """This is an example description of the test."""
        self.fail()

Then when Sphinx generates documentation for this test case, the HTML
will actually show as if the test case were documented like this::

    @quarantined('JIRA-123')
    def example_test(self):
        """This is an example description of the test. (Quarantined: JIRA-123)"""
        self.fail()

If documentation is autogenerated on a merge to master, and a test is
decorated with that same merge, then the documentation will always show
the most up to date status of each test case.

This feature can be disabled by adding the following lines to your
Sphinx ``conf.py`` file::

    # Disable test method docstring hacking in decorators
    from qe_tools.opencafe import decorators
    decorators.disable_docstring_hacking()


**Applying Decorators To Specific Environments**

Most of the decorators in this module can be applied to only specified
environments. This is useful if say a test is only broken in the staging
environment.

In order to utilize this functionality, your OpenCafe test fixture must
tell the decorators how to know in which environment the tests are currently
being executed.

A specific method must be implemented on the test fixture that takes a
single string argument, and it should return a boolean value that shows
whether or not the given string argument value matches the name of the
environment in which OpenCafe tests are currently being executed.

The name of this method must match the ``ENVIRONMENT_MATCHING_METHOD_NAME``
constant defined in this module.
'''

# Standard Library
from atexit import register
from inspect import isclass
from os import environ
import re
from traceback import format_stack
from unittest import skip, SkipTest
# OpenCafe
from cafe.drivers.unittest.decorators import tags as _cafe_tags
# OpenCafe doesn't provide a way to reset tags :-(, so we have to import
# these attribute names so that we don't have to duplicate them.
from cafe.drivers.unittest.decorators import (TAGS_DECORATOR_TAG_LIST_NAME,
                                              PARALLEL_TAGS_LIST_ATTR)


#############
# CONSTANTS #
#############

ENVIRONMENT_MATCHING_METHOD_NAME = 'current_environment_matches'
'''The name of the method to implement on the test fixture for environment functionality.

This method must be implemented in order to utilize environment
related decorator functionality.

NOTE: This method is called when the decorators are being run,
so it must be a @staticmethod.
'''

JIRA_REGEX = re.compile('^[A-Z]+-[0-9]+$')
'''A regular expression that matches a valid JIRA ID.'''

COVERAGE_TAG_DECORATOR_TAG_LIST_NAME = '__coverage_report_tags__'
'''Name of the field we add to all tagged tests that tracks tags for coverage reporting.
See the tags decorator documentation for why we are doing this.
'''

COVERAGE_REPORT_FILE_NAME = None

_TAGS_INFO_DIR_NAME = environ.get('COLLECT_TAGS_DATA_INTO', None)
if _TAGS_INFO_DIR_NAME is None:
    # Tags logging function for when we are _not_ collecting/logging tags info.
    def _tags_log_info(func):
        '''No logging decorator, just return the function'''
        return func
else:
    import json
    from tempfile import NamedTemporaryFile

    _coverage_report_file = NamedTemporaryFile(mode='w', suffix='.json', prefix='coverage-',
                                               dir=_TAGS_INFO_DIR_NAME, delete=False)

    # Make sure the file is closed on interpreter exit.
    register(_coverage_report_file.close)

    # We're going to do a cheap-o jsonlines like solution here, each test
    # will dump out a one-line json object for reporting.
    def _tags_log_info(func):
        '''logging decorator that log tags info, but doesn't run func'''
        # Implementation note:
        # The insight here is that the decorator is returning a whole different function,
        # which can extract data from 'func', but which is not obligated to call 'func'.
        # This makes for a 'safe' full run (no dry-run needed) and greatly simplifies the
        # code for extracting data.
        def _logging_only(*args, **kwargs):
            tags_data = dict()
            test_obj = args[0]
            tags_data['test'] = func.__name__
            tags_data['doc'] = func.__doc__
            tags_data['provenance'] = (test_obj.__class__.__module__.split('.') +
                                       [test_obj.__class__.__name__])
            tags_data['tags'] = _get_coverage_tags_from(func)
            json.dump(tags_data, _coverage_report_file, sort_keys=True)
            _coverage_report_file.write('\n')
            # It's annoying to have to flush all the time, but when I tried putting
            # flush 'atexit' time, it didn't work. I didn't dig deeply in to why.
            _coverage_report_file.flush()
        return _logging_only


# INTERIM LIST!
# This *must* come from coverage.rst and table read as a FF on this code.
STATUS_TAGS = set('nyi not-tested needs-work quarantined'.split())

############
# SETTINGS #
############

_docstring_hacking_enabled = True
'''The default setting for whether or not the docstring hacking feature should be enabled.'''


def disable_docstring_hacking():
    '''Disable this module's docstring hacking feature.'''
    global _docstring_hacking_enabled
    _docstring_hacking_enabled = False


###########
# HELPERS #
###########

def _print_and_raise(exc_type, message):
    '''Print message and raise exception.

    This is needed because an OpenCAFE bug hides exceptions raised
    during module load (which is when decorators are run),
    so to aid the test writer, print the message and then raise
    the exception.
    '''
    print('\nERROR:\n{}\n'.format(message))
    # Skip showing format_stack itself, and this function (neither are helpful).
    print(''.join(format_stack()[:-2]))
    raise exc_type(message)


def _add_text_to_docstring_summary_line(original_docstring, summary_line_addition):
    '''
    Add text to the summary line of the given docstring.

    Args:
        original_docstring (str): The original docstring to be amended.
        summary_line_addition (str): The string to append to end of the docstring's summary line

    Returns:
        str: An updated docstring.
    '''
    text_addition = ' ({0})'.format(summary_line_addition)

    if original_docstring is None:
        docstring_lines = ['<No docstring provided>']
    else:
        docstring_lines = original_docstring.splitlines()

    # The summary line may be on the same line as the starting triple quote,
    # or it may be on the line below. Handle both cases.
    if docstring_lines[0]:
        docstring_lines[0] += text_addition
    elif docstring_lines[1]:
        docstring_lines[1] += text_addition
    else:
        docstring_lines[0] = '<Malformed docstring>' + text_addition

    return '\n'.join(docstring_lines)


def _all_jira_ids_in(s):
    '''
    Return a list of all the non-overlapping JIRA IDs contained in s.

    Args:
        s (str): The string to be searched for JIRA IDs

    Returns:
        A list of all the JIRA ID strings found.
    '''
    return JIRA_REGEX.findall(s)


def _clear_cafe_tags_from(func):
    '''Clear out all the cafe tags on func'''
    for attr in (TAGS_DECORATOR_TAG_LIST_NAME, PARALLEL_TAGS_LIST_ATTR):
        if hasattr(func, attr):
            delattr(func, attr)


def _get_coverage_tags_from(func):
    '''Return the coverage tags from func, setting to empty list if needed.'''
    if not getattr(func, COVERAGE_TAG_DECORATOR_TAG_LIST_NAME, None):
        setattr(func, COVERAGE_TAG_DECORATOR_TAG_LIST_NAME, [])
    return getattr(func, COVERAGE_TAG_DECORATOR_TAG_LIST_NAME)


def _add_tags(func, cafe_tags=tuple(), coverage_tags=tuple()):
    '''
    Add the given tags to the given function, both cafe tags and coverage tags.

    Args:
        func: the function to decorate with tagging information.
        cafe_tags: iterable of cafe tags to add to func.
        coverage_tags: iterable of coverage tags to add to func.

    Returns:
        The decorated function.
    '''
    func = _cafe_tags(*cafe_tags)(func)
    _get_coverage_tags_from(func).extend(coverage_tags)
    return func


def _cafe_tag_prefix(status_tag, target_tag):
    '''Optionally prefix target_tag with status_tag to work-around OpenCAFE tag filtering.

    Args:
        status_tag (str): the status tag to be used as a prefix, if needed.
        target_tag (str): another tag to be potentially mutated.

    Returns:
        cafe-friendly version of target_tag
    '''

    if (target_tag == status_tag) or JIRA_REGEX.match(target_tag):
        return target_tag
    return '{}-{}'.format(status_tag, target_tag)


def _mutate_tags_for_cafe(tags_list):
    '''Implement the tag mutation as described in the `tags` decorator.

    Args:
        tags_list (iterable of str): The list of tags to (potentially) mutate.

    Returns:
        List of (potentially) mutated tags

    Raises:
        ValueError if more than one Status tag has been used.
    '''

    actual_status_tags = set(tags_list) & STATUS_TAGS

    # If there are no status tags in use, there is no need to mutate any
    # of the tags, so we can use them just as they are.
    if not actual_status_tags:
        return tags_list

    if len(actual_status_tags) > 1:
        overlapping_tags = sorted(actual_status_tags)
        msg = 'Conflicting Status tags, only one permitted: {}'.format(', '.join(overlapping_tags))
        _print_and_raise(ValueError, msg)

    status_tag = actual_status_tags.pop()
    new_tags = []
    for a_tag in tags_list:
        new_tags.append(_cafe_tag_prefix(status_tag, a_tag))
    return new_tags


def _environment_matches(test_fixture, environment):
    '''
    Determine if a given environment matches the current test environment.

    Args:
        test_fixture: The class or class instance for the test or class that was decorated.
        environment (str): The environment to compare against the current test environment.

    Returns:
        bool: Whether or not the current test environment matches the given environment.

    Raises:
        NotImplementedError: If no environment matching method is implemented on the
        test fixture.
    '''
    environment_matching_method = getattr(test_fixture, ENVIRONMENT_MATCHING_METHOD_NAME, None)

    if environment_matching_method is None:
        _print_and_raise(NotImplementedError,
                         'In order to utilize the this decorator functionality, '
                         'you must implement a "{0}" method that determines whether '
                         'or not the current environment matches the environment '
                         'affected by this decorator.'
                         ''.format(ENVIRONMENT_MATCHING_METHOD_NAME))

    return environment_matching_method(environment)


def _get_decorator_for_skipping_test(reason, details, tag_name, environment_affected=''):
    '''
    Get a decorator that skips a test for a specific reason.

    If an ``environment_affected`` value is provided, then the decorator will
    only be applied if the provided value matches the environment being tested.
    Otherwise, it will assume that the decorator should be applied no matter the
    environment.

    Note:
        If an ``environment_affected`` value is provided to the original decorator,
        then an environment matching method **MUST** be implemented on the test fixture.
        The details string must contain one or more JIRA-IDs that provide traceability for
        why this test would be skipped.

    Args:
        reason (str): The short reason why the test should be skipped.
        details (str): More details on the specific reason a test is being skipped.
        tag_name (str): The name of the OpenCafe tag that should be applied with the decorator.
        environment_affected (str): The specific environment that is affected by this decorator.
            If none is provided, the decorator is applied no matter the environment.

    Returns:
        A decorator function into which to pass the test case or test class.

    Raises:
        ValueError: If the details string does not contain something that resembles a JIRA ID.
    '''

    jira_ids = _all_jira_ids_in(details)
    if not jira_ids:
        _print_and_raise(ValueError, '"{0}" does not contain any JIRA IDs.'.format(details))

    if environment_affected:
        message = '{0} (in {1} environment): {2}'.format(reason, environment_affected, details)
    else:
        message = '{0}: {1}'.format(reason, details)

    def decorator(test_case_or_class):
        '''The decorator with which to decorate the test case or class.'''
        if isclass(test_case_or_class):
            if not environment_affected or _environment_matches(test_fixture=test_case_or_class,
                                                                environment=environment_affected):
                return skip(message)(test_case_or_class)

            return test_case_or_class

        def wrapper(self, *args, **kwargs):
            '''The new function with which to replace the original test case.'''
            if not environment_affected or _environment_matches(test_fixture=self,
                                                                environment=environment_affected):
                raise SkipTest(message)

            return test_case_or_class(self, *args, **kwargs)

        if _docstring_hacking_enabled:
            wrapper.__doc__ = _add_text_to_docstring_summary_line(
                original_docstring=test_case_or_class.__doc__, summary_line_addition=message)
        else:
            wrapper.__doc__ = test_case_or_class.__doc__

        wrapper.__name__ = test_case_or_class.__name__

        tags = [tag_name] + jira_ids
        wrapper = _add_tags(wrapper, cafe_tags=tags, coverage_tags=tags)

        return wrapper

    return decorator


##############
# DECORATORS #
##############


def quarantined(details, environment_affected=None):
    '''
    Mark a test case as quarantined, and skip the test case.

    This should be used for test cases that are not functioning properly
    due to an issue with the system being tested that is outside the scope
    of the QE team.

    The ``details`` parameter should include the ID for the JIRA story.
    If no ID exists, a JIRA issue/defect should be created before marking
    the test as quarantined.

    Args:
        details (str): Information about why the test is quarantined.
        environment_affected (str): The only environment in which the decorator applies.

    Returns:
        A decorator function into which to pass the test case or test class.
    '''
    return _get_decorator_for_skipping_test(
        reason='Quarantined', details=details, tag_name='quarantined',
        environment_affected=environment_affected)


def needs_work(details, environment_affected=None):
    '''
    Mark a test case as needs work and skip the test case.

    This should be used for test cases that are not functioning properly
    due to an issue with the test or test framework. This issue should
    be something that will be fixed by the QE team.

    The ``details`` parameter should include the ID for the JIRA story.
    If no ID exists, a JIRA issue/defect should be created before marking
    the test as needs work.

    Args:
        details (str): Information about why the test needs work.
        environment_affected (str): The only environment in which the decorator applies.

    Returns:
        A decorator function to pass the test case or test class into.
    '''
    return _get_decorator_for_skipping_test(
        reason='Needs Work', details=details, tag_name='needs-work',
        environment_affected=environment_affected)


def not_tested(details, environment_affected=None):
    '''
    Mark a test case as not tested and skip the test case.

    This should be used for test cases that are implemented, but the
    service being tested is not ready.

    The ``details`` parameter should include the ID for the JIRA story
    designated for making this service ready.

    Args:
        details (str): Information about why the test cannot be run yet.
        environment_affected (str): The only environment in which the decorator applies.

    Returns:
        A decorator function to pass the test case or test class into.
    '''
    return _get_decorator_for_skipping_test(
        reason='Not Tested - Service Not Ready', details=details,
        tag_name='not-tested', environment_affected=environment_affected)


def nyi(details):
    '''
    Mark a test case or class as not implemented, and skip the test case.

    The ``details`` parameter should include the ID for the JIRA story
    designated for implementing this test.

    Args:
        details (str): Information about why the test is not implemented.
            Typically with ``@nyi``, only the JIRA ID is included,
            but any other details are welcome.

    Returns:
        A decorator function to pass the test case or test class into.
    '''
    return _get_decorator_for_skipping_test(reason='Not Implemented', details=details,
                                            tag_name='nyi',)


def only_in(environment, reason=None):
    '''
    Skip a test case or class if the given environment matches the current test environment.

    Args:
        environment (str): The environment in which the test case or class
            is allowed to run.
        reason (str): The reason why the test case or class must be only
            run in the given environment.

    Note:
        In order to use this decorator, an environment matching method **MUST**
        be implemented on the test fixture. This method should return a boolean
        value that shows whether or not the current environment matches the
        requested environment affected.

    Returns:
        A decorator function to pass the test case or test class into.
    '''
    message = 'Only test in {0}'.format(environment)
    if reason:
        message += ': {0}'.format(reason)

    def decorator(test_case_or_class):
        '''
        Replace the given class or method with a function that may skip the original logic.

        Args:
            test_case_or_class: The original test method or test class being decorated.

        Returns:
            Callable: A replacement class or method that is skipped if the correct
            environment is not being tested.
        '''
        if isclass(test_case_or_class):
            if _environment_matches(test_fixture=test_case_or_class, environment=environment):
                return test_case_or_class

            return skip(message)(test_case_or_class)

        def wrapper(self, *args, **kwargs):
            '''The new function with which to replace the original test case.'''
            if _environment_matches(test_fixture=self, environment=environment):
                return test_case_or_class(self, *args, **kwargs)

            raise SkipTest(message)

        if _docstring_hacking_enabled:
            wrapper.__doc__ = _add_text_to_docstring_summary_line(
                original_docstring=test_case_or_class.__doc__, summary_line_addition=message)
        else:
            wrapper.__doc__ = test_case_or_class.__doc__

        wrapper.__name__ = test_case_or_class.__name__

        return wrapper

    return decorator


def production_only(reason=None):
    '''
    Mark a test case as production only and skip the test if in a staging environment.

    Args:
        reason (str): The reason why the test case or class should only be run in 'production'.

    Returns:
        A decorator function to pass the test case or test class into.
    '''
    return only_in(environment='Production', reason=reason)


def staging_only(reason=None):
    '''
    Mark a test case as staging only and skip the test if not in a staging environment.

    Args:
        reason (str): The reason why the test case or class should only be run in 'staging'.

    Returns:
        A decorator function to pass the test case or test class into.
    '''
    return only_in(environment='Staging', reason=reason)


def tags(*tags_list):
    '''
    Create a decorator that applies the given `tags_list` tags to the decorated function.

    Args:
        tags_list (tuple): tags to be added.

    Returns:
        A decorator function that will add the given tags.

    NOTE:
        This decorator generator must be outermost of all the decorators in this file.

        This decorator generator will also mutate the cafe tags so that anything other
        than the status tag and a JIRA tag will have a non-operational status tag prepended to it.
        This is overcome a limitation in the cafe test runner that cannot use tags to exclude tests.
        So to accomplish this, a test that is tagged with both 'nyi' and 'regression' will have it's
        cafe tags changed to be 'nyi' and 'nyi-regression' so that any test run as `-t regression`
        will _not_ be able to select this test. This is handy, esp. in the case of quarantined tags
        where it might be desireable to run quarantined-smoke tests on a regular basis. It seems
        unlikely that running nyi-<anything> tests would be useful, but it would be possible.
    '''

    tags_list = list(tags_list)  # make sure it is a re-useable iterable.

    def tag_decorator(func):
        total_tags = _get_coverage_tags_from(func) + tags_list
        cafe_tags = _mutate_tags_for_cafe(total_tags)
        _clear_cafe_tags_from(func)

        func = _add_tags(func, cafe_tags=cafe_tags, coverage_tags=tags_list)

        return _tags_log_info(func)

    return tag_decorator
