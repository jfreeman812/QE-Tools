"""
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

    @quarantined("JIRA-123")
    def example_test(self):
        '''This is an example description of the test.'''
        self.fail()

Then when Sphinx generates documentation for this test case, the HTML
will actually show as if the test case were documented like this::

    @quarantined("JIRA-123")
    def example_test(self):
        '''This is an example description of the test. (Quarantined: JIRA-123)'''
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
"""

# Standard Library
from inspect import isclass
import re
from unittest import skip, SkipTest
# OpenCafe
from cafe.drivers.unittest.decorators import tags as cafe_tags


#############
# CONSTANTS #
#############

# All standard tag names come from https://pages.github.rackspace.com/QualityEngineering/QE-Tools/coverage.html
EXECUTION_METHOD_TAG_NAMES = ["manual", "automated"]
POLARITY_TAG_NAMES = ["positive", "negative"]
PRIORITY_TAG_NAMES = ["p0", "p1", "p2"]
STATUS_TAG_NAMES = ["nyi", "not-tested", "needs-work", "quarantined", "operational"]
SUITE_TAG_NAMES = ["deploy", "smoke", "load", "solo", "integration", "security"]

ENVIRONMENT_MATCHING_METHOD_NAME = "current_environment_matches"
"""The name of the method that must be implemented in order to utilize environment related decorator functionality."""

JIRA_REGEX = re.compile("^[A-Z]+-[0-9]+$")
"""A regular expression that matches a valid JIRA ticket reference."""


############
# SETTINGS #
############

_docstring_hacking_enabled = True
"""The default setting for whether or not the docstring hacking feature should be enabled."""


def disable_docstring_hacking():
    """Disable this module's docstring hacking feature."""
    global _docstring_hacking_enabled
    _docstring_hacking_enabled = False


###########
# HELPERS #
###########

def _add_text_to_docstring_summary_line(original_docstring, summary_line_addition):
    """
    Add text to the summary line of the given docstring.

    Args:
        original_docstring (str): The original docstring to be amended.
        summary_line_addition (str): The string to append to end of the docstring's summary line

    Returns:
        str: An updated docstring.
    """
    text_addition = " ({0})".format(summary_line_addition)

    docstring_lines = original_docstring.split("\n")

    # The summary line may be on the same line as the starting triple quote,
    # or it may be on the line below. Handle both cases.
    if docstring_lines[0]:
        docstring_lines[0] += text_addition
    else:
        docstring_lines[1] += text_addition

    return "\n".join(docstring_lines)


def _confirm_that_string_contains_a_jira_ticket_reference(s):
    """
    Confirm that somewhere in a string, there is something that resembles a JIRA ticket.

    Basically there needs to be something that starts with some all caps letters
    followed by a dash followed by a number.

    Args:
        s (str): The string that should have a JIRA ticket number in it.

    Raises:
        ValueError: If the string does not contain something that resembles a JIRA ticket.
    """
    for word in s.split():
        # The JIRA reference can be surrounded by any of these characters on either side.
        if JIRA_REGEX.match(word.strip(".,![]{}()")):
            return

    raise ValueError("'{0}' does not contain a JIRA ticket reference.".format(s))


def _environment_matches(test_fixture, environment):
    """
    Determine if a given environment matches the current test environment.

    Args:
        test_fixture: The class or class instance for the test or class that was decorated.
        environment (str): The environment to compare against the current test environment.

    Returns:
        bool: Whether or not the current test environment matches the given environment.

    Raises:
        NotImplementedError: If no environment matching method is implemented on the
        test fixture.
    """
    environment_matching_method = getattr(test_fixture, ENVIRONMENT_MATCHING_METHOD_NAME, None)

    if environment_matching_method is None:
        raise NotImplementedError("In order to utilize the this decorator functionality, you must "
                                  "implement a '{0}' method that determines whether or not the current "
                                  "environment matches the environment affected by this decorator."
                                  "".format(ENVIRONMENT_MATCHING_METHOD_NAME))

    return environment_matching_method(environment)


def _get_decorator_for_skipping_test(reason, details, tag_name, environment_affected=""):
    """
    Get a decorator that skips a test for a specific reason.

    If an ``environment_affected`` value is provided, then the decorator will
    only be applied if the provided value matches the environment being tested.
    Otherwise, it will assume that the decorator should be applied no matter the
    environment.

    Note:
        If an ``environment_affected`` value is provided to the original decorator,
        then an environment matching method **MUST** be implemented on the test fixture.

    Args:
        reason (str): The short reason why the test should be skipped.
        details (str): More details on the specific reason a test is being skipped.
        tag_name (str): The name of the OpenCafe tag that should be applied with the decorator.
        environment_affected (str): The specific environment that is affected by this decorator. If
            none is provided, the decorator is applied no matter the environment.

    Returns:
        A decorator function into which to pass the test case or test class.
    """
    if environment_affected:
        message = "{0} (in {1} environment): {2}".format(reason, environment_affected, details)
    else:
        message = "{0}: {1}".format(reason, details)

    def decorator(test_case_or_class):
        """The decorator with which to decorate the test case or class."""
        if isclass(test_case_or_class):
            if not environment_affected or _environment_matches(test_fixture=test_case_or_class,
                                                                environment=environment_affected):
                return skip(message)(test_case_or_class)

            return test_case_or_class

        def wrapper(self, *args, **kwargs):
            """The new function with which to replace the original test case."""
            if not environment_affected or _environment_matches(test_fixture=self,
                                                                environment=environment_affected):
                raise SkipTest(message)

            return test_case_or_class(self, *args, **kwargs)

        if _docstring_hacking_enabled:
            wrapper.__doc__ = _add_text_to_docstring_summary_line(
                original_docstring=test_case_or_class.__doc__, summary_line_addition=message)

        wrapper = cafe_tags(tag_name)(wrapper)

        return wrapper

    return decorator


##############
# DECORATORS #
##############


def tags(*tags, **attrs):
    """
    Add tags and attributes that are interpreted by OpenCafe at run time.

    The given tags go through a series of checks. If no polarity tag is
    provided, then a ``ValueError`` is raised. For each of the other tag
    categories, if no tag for that category is provided, then the default
    is assigned. Lastly, "non-" tags are added for the suites that do not
    apply to the test method.

    After these checks and additions are complete, the standard OpenCafe
    ``tags`` decorator is applied.

    Args:
        *tags: The tags to be included with the test case.
        **attrs: Attributes to be added to the test case.

    Returns:
        Callable: The newly decorated test case method.

    Raises:
        ValueError: If no polarity tag is provided.
    """
    tags = list(tags)

    if not set(tags).intersection(set(POLARITY_TAG_NAMES)):
        raise ValueError("One of the following polarity tags must be provided: {0}"
                         "".format(POLARITY_TAG_NAMES))

    # Tag the test with the default execution method if none is provided
    if not set(tags).intersection(set(EXECUTION_METHOD_TAG_NAMES)):
        tags.append("automated")

    # Tag the test with the default priority if none is provided
    if not set(tags).intersection(set(PRIORITY_TAG_NAMES)):
        tags.append("p1")

    # Tag the test with the default status if none is provided
    if not set(tags).intersection(set(STATUS_TAG_NAMES)):
        tags.append("operational")

    # Add "non" tags for all suites that don't apply to the test
    for tag_name in SUITE_TAG_NAMES:
        if tag_name not in tags:
            tags.append("non-{0}".format(tag_name))

    return cafe_tags(*tags, **attrs)


def quarantined(details, environment_affected=None):
    """
    Mark a test case as quarantined, and skip the test case.

    This should be used for test cases that are not functioning properly
    due to an issue with the system being tested that is outside the scope
    of the QE team.

    The ``details`` parameter should include the label for the JIRA story.
    If no label exists, a JIRA ticket should be created before marking
    the test as quarantined.

    Args:
        details (str): Information about why the test is quarantined.
        environment_affected (str): The only environment in which the decorator applies.

    Returns:
        A decorator function into which to pass the test case or test class.
    """
    _confirm_that_string_contains_a_jira_ticket_reference(details)
    return _get_decorator_for_skipping_test(reason="Quarantined", details=details, tag_name="quarantined",
                                            environment_affected=environment_affected)


def needs_work(details, environment_affected=None):
    """
    Mark a test case as needs work and skip the test case.

    This should be used for test cases that are not functioning properly
    due to an issue with the test or test framework. This issue should
    be something that will be fixed by the QE team.

    The ``details`` parameter should include the label for the JIRA story.
    If no label exists, a JIRA ticket should be created before marking
    the test as needs work.

    Args:
        details (str): Information about why the test needs work.
        environment_affected (str): The only environment in which the decorator applies.

    Returns:
        A decorator function to pass the test case or test class into.
    """
    _confirm_that_string_contains_a_jira_ticket_reference(details)
    return _get_decorator_for_skipping_test(reason="Needs Work", details=details, tag_name="needs-work",
                                            environment_affected=environment_affected)


def not_tested(details, environment_affected=None):
    """
    Mark a test case as not tested and skip the test case.

    This should be used for test cases that are implemented, but the
    service being tested is not ready.

    The ``details`` parameter should include the label for the JIRA story
    designated for making this service ready.

    Args:
        details (str): Information about why the test cannot be run yet.
        environment_affected (str): The only environment in which the decorator applies.

    Returns:
        A decorator function to pass the test case or test class into.
    """
    _confirm_that_string_contains_a_jira_ticket_reference(details)
    return _get_decorator_for_skipping_test(reason="Not Tested - Service Not Ready", details=details,
                                            tag_name="not-tested", environment_affected=environment_affected)


def nyi(details):
    """
    Mark a test case or class as not implemented, and skip the test case.

    The ``details`` parameter should include the label for the JIRA story
    designated for implementing this test.

    Args:
        details (str): Information about why the test is not implemented. Typically with ``@nyi``,
            only the JIRA reference is included, but any other details are welcome.

    Returns:
        A decorator function to pass the test case or test class into.
    """
    _confirm_that_string_contains_a_jira_ticket_reference(details)
    return _get_decorator_for_skipping_test(reason="Not Implemented", details=details, tag_name="nyi",)


def only_in(environment, reason=None):
    """
    Skip a test case or class if the given environment matches the current test environment.

    Args:
        environment (str): The environment in which the test case or class is allowed to run.
        reason (str): The reason why the test case or class must be only run in the given environment.

    Note:
        In order to use this decorator, an environment matching method **MUST** be implemented
        on the test fixture. This method should return a boolean value that shows whether or
        not the current environment matches the requested environment affected.

    Returns:
        A decorator function to pass the test case or test class into.
    """
    message = "Only test in {0}".format(environment)
    if reason:
        message += ": {0}".format(reason)

    def decorator(test_case_or_class):
        """
        Replace the given class or method with a function that may skip the original logic.

        Args:
            test_case_or_class: The original test method or test class being decorated.

        Returns:
            Callable: A replacement class or method that is skipped if the correct environment is not being tested.
        """
        if isclass(test_case_or_class):
            if _environment_matches(test_fixture=test_case_or_class, environment=environment):
                return test_case_or_class

            return skip(message)(test_case_or_class)

        def wrapper(self, *args, **kwargs):
            """The new function with which to replace the original test case."""
            if _environment_matches(test_fixture=self, environment=environment):
                return test_case_or_class(self, *args, **kwargs)

            raise SkipTest(message)

        if _docstring_hacking_enabled:
            wrapper.__doc__ = _add_text_to_docstring_summary_line(
                original_docstring=test_case_or_class.__doc__, summary_line_addition=message)

        return wrapper

    return decorator


def production_only(reason=None):
    """
    Mark a test case as production only and skip the test if in a staging environment.

    This is the equivalent of writing this at the beginning of a test case::

        if self.client.environment.lower() != "production":
            self.skipTest(reason)

    Args:
        reason (str): The reason why the test case or class should only be run in staging.

    Returns:
        A decorator function to pass the test case or test class into.
    """
    return only_in(environment="Production", reason=reason)


def staging_only(reason=None):
    """
    Mark a test case as staging only and skip the test if not in a staging environment.

    This is the equivalent of writing this at the beginning of a test case::

        if self.client.environment.lower() != "staging":
            self.skipTest(reason)

    Args:
        reason (str): The reason why the test case or class should only be run in staging.

    Returns:
        A decorator function to pass the test case or test class into.
    """
    return only_in(environment="Staging", reason=reason)
