'''
A collection of helpers layered on top of Python logging for QE logging standards.

``setup_logging()`` is handy helper to create log files in well- known and standard QE locations.

``behave_logging`` is a module to help with logging in behave testing.

``no_logging`` is a module to supress logging, such as might be useful
in utility scripts.

``requests_client_logging`` is a module that provides a drop-in replacement for
``requests.Session`` that ties ``requests`` to ``requests_logging``, plus a few other handy things.

``requests_logging`` is a module to help with logging in requests API testing.

As an aid for debugging, this module also provides a way to
include logging output on the console. This can be handy for
when logging is being captured (such as by Behave or OpenCAFE)
or suppressed in a utility program (see no_logging).
If you set the environment variable DEBUG_WATCH_LOG, a root level
handler will be created that prints the logging output
to standard error. (It does not matter what
the environment variable is set to, just that it is set.)
'''


import logging
import os
from datetime import datetime


DEFAULT_LOG_DIRECTORY = 'logs'
DEFAULT_FORMATTER_STRING = '%(asctime)s:%(levelname)-8s:%(name)-25s:%(message)s'


if 'DEBUG_WATCH_LOG' in os.environ:
    _handler = logging.StreamHandler()
    _handler.setLevel(logging.DEBUG)
    logging.getLogger().addHandler(_handler)


def setup_logging(log_name_prefix, *historical_log_dir_layers, **kwargs):
    '''
    Setup logging file handlers with a standard format for QE logging.

    One handler will be set to write in the base log directory,
    the other in the historical log dir layers (if provided) with time stamped directories.

    Note:
        For historical reasons, ``setup_logging`` will set up handlers only
        if no root level file handlers are already defined.

    Args:
        log_name_prefix (str): The prefix for the log file name, prepended to .master.log.
        *historical_log_dir_layers (str):   Additional directory layers if desired for the
            historical log directories and files.
            One use case for this is providing the test environment as
            ``*historical_log_dir_layers`` resulting in the time stamped directories being grouped
            by test environment.
        **kwargs:  Additional keyword arguments, valid options are ``base_log_dir`` and
            ``formatter``.
            The default ``base_log_dir`` of 'logs' can be overridden if desired to have the logs
            placed in an alternate location.
            The default ``formatter`` can be overridden if desired by passing in an
            logging.Formatter instance.

    Returns:
        List[str]: log-file filenames that were created, or the empty list if none were created.

    Examples:
        >>> import logging
        >>> from qe_logging import setup_logging
        >>> setup_logging('QE_LOGS', base_log_dir='logs_dir')
        >>> logging.getLogger('Bubba Logger').critical('Urgent Message!')
        Writes files:
        logs_dir/QE_LOGS.master.log
            YYYY-MM-DD HH:MM:SS,FFF:CRITICAL:Bubba Logger             :Urgent Message!
        logs_dir/YYYY-MM-DD_HH_MM_SS.FFFFFF/QE_LOGS.master.log
            YYYY-MM-DD HH:MM:SS,FFF:CRITICAL:Bubba Logger             :Urgent Message!

        >>> import logging
        >>> from qe_logging import setup_logging
        >>> setup_logging('QET', 'some_layer', 'another_layer', base_log_dir='logs_dir')
        >>> logging.getLogger('SOME LOGGER').critical('LOOK AT ME')
        Writes files:
        logs_dir/QET.master.log
            YYYY-MM-DD HH:MM:SS,FFF:CRITICAL:SOME LOGGER              :LOOK AT ME
        logs_dir/some_layer/another_layer/YYYY-MM-DD_HH_MM_SS.FFFFFF/QET.master.log
            YYYY-MM-DD HH:MM:SS,FFF:CRITICAL:SOME LOGGER              :LOOK AT ME
    '''
    # The following two kwargs can be moved into the function call once python 2 support is ended.
    base_log_dir = kwargs.get('base_log_dir', DEFAULT_LOG_DIRECTORY)
    formatter = kwargs.get('formatter', logging.Formatter(DEFAULT_FORMATTER_STRING))

    root_log = logging.getLogger('')

    result = []

    # Only add our own FileHandler loggers if none are already present.
    if any(isinstance(x, logging.FileHandler) for x in root_log.handlers):
        return result

    timestamp = '{:%Y%m%d_%H%M%S}'.format(datetime.now())
    timestamp_log_dir = os.path.join(*((base_log_dir,) + historical_log_dir_layers + (timestamp,)))
    master_log_filename = '{}.master.log'.format(log_name_prefix.lower())

    for dir_ in (timestamp_log_dir, base_log_dir):
        if not os.path.exists(dir_):
            os.makedirs(dir_)

        log_filename = os.path.join(dir_, master_log_filename)
        result.append(log_filename)

        # Set mode to 'w' so that any known file name log file is reset.
        # Previous logs will still be available in their timestamped directories.
        log_handler = logging.FileHandler(log_filename, mode='w', encoding='UTF-8')
        log_handler.setFormatter(formatter)
        root_log.addHandler(log_handler)

    return result
