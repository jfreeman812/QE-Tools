'''
Logging for Behave testing.

This module defines environment style functions for adding behave data
to your log files. It's often hard to read a raw log file and tell which
lines belong to, or were caused by, which step of which scenario.
The functions in this module echo the function names used in a normal
behave environment.py file so that you can easily call them from the
same functions there. For consistency, and ease of use, these before/after
functions take the same parameters as the functions in the
environment.py file.

Notes:
    By importing this module, various behave loggers will be created and their log
    levels set to DEBUG. This captures all logging from any 'behave' logger in our log files
    while still permitting the behave command-line logging parameters to operate, as
    expected, to control the level of capturing displayed on step faliure.
    If behave's logcapture is turned off all 'behave' logger output is also displayed on the console
    during a run, regardless of the log level set on from the command line (or config file).
'''

import logging

from qe_logging import setup_logging


logging.getLogger('behave').setLevel(logging.DEBUG)

_all_debug = logging.getLogger('behave.all').debug
_feature_debug = logging.getLogger('behave.feature').debug
_scenario_debug = logging.getLogger('behave.scenario').debug
_step_debug = logging.getLogger('behave.step').debug


def before_all(context, *args, **kwargs):
    '''
    Will setup the QE logging for Behave testing.

    This should be called in the ``before_all`` in the environment file.

    ``config.qe_behave_logging_filenames`` is set to the result of the
    base_logging.setup_logging call.

    Note:
        ``context.config.setup_logging`` will be called with no parameters
        before base_logging.setup_logging is called with \*args and \*\*kwargs.

    Args:
        context (behave.Context): A Behave context object.
        *args: Additional arguments passed to base_logging.setup_logging function.
        \**kwargs: Additional keyword arguments passed to base_logging.setup_logging function.
    '''
    context.config.setup_logging()  # Handle the logging switches from the behave command-line
    context.qe_behave_logging_filenames = setup_logging(*args, **kwargs)


def before_feature(context, feature):
    '''
    Logs the feature name.

    This should be called in the ``before_feature`` in the environment file.

    Args:
        context (behave.Context): A Behave context object.
        feature (behave.Feature):  A Behave feature object.
    '''
    _feature_debug('Feature: {}'.format(feature.name))


def before_scenario(context, scenario):
    '''
    Logs the scenario name.

    This should be called in the ``before_scenario`` in the environment file.

    Args:
        context (behave.Context): A Behave context object.
        scenario (behave.Scenario):  A Behave scenario object.
    '''
    _scenario_debug('    Scenario: {}'.format(scenario.name))


def before_step(context, step):
    '''
    Logs the step keyword and name.

    This should be called in the ``before_step`` in the environment file.

    Args:
        context (behave.Context): A Behave context object.
        step (behave.Step):  A Behave step object.
    '''
    _step_debug('        {} {}'.format(step.keyword, step.name))


def after_step(context, step):
    '''
    Logs failure info for a Behave step.

    This should be called in the ``after_step`` in the environment file.

    Args:
        context (behave.Context): A Behave context object.
        step (behave.Step):  A Behave step object.
    '''
    if step.status == 'failed':
        _step_debug('        FAILED: {} {}'.format(step.keyword, step.name))
        _step_debug('                {}'.format(step.error_message))
        _step_debug('--------END OF FAILURE DEBUGGING')
    _step_debug('')


def after_scenario(context, scenario):
    '''
    Logs a line break after the scenario ends.

    This should be called in the ``after_scenario`` in the environment file.

    Args:
        context (behave.Context): A Behave context object.
        scenario (behave.Scenario):  A Behave scenario object.
    '''
    _scenario_debug('')


def after_feature(context, feature):
    '''
    Logs a line break after the feature ends.

    This should be called in the ``after_feature`` in the environment file.

    Args:
        context (behave.Context): A Behave context object.
        feature (behave.Feature):  A Behave feature object.
    '''
    _feature_debug('')


def after_all(context):
    '''
    Logs that this function was called. (For completeness and symmetry)

    Args:
        context (behave.Context): A Behave context object.
    '''
    _all_debug('')
    _all_debug('after_all - end of testing')
