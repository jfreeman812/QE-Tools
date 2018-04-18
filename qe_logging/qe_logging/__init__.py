import logging
import os
from datetime import datetime


DEFAULT_LOG_DIRECTORY = 'logs'
DEFAULT_FORMATTER_STRING = '%(asctime)s:%(levelname)-8s:%(name)-25s:%(message)s'


def setup_logging(log_name_prefix, *historical_log_dir_layers, **kwargs):
    '''
    Will setup logging file handlers with a standard format for QE logging.

    One handler will be set to write in the base log directory, the other in the historical log dir
    layers (if provided) with time stamped directories.

    Args:
        log_name_prefix (str): The prefix for the log file name, prepended to .master.log.
        *historical_log_dir_layers (str):   Additional directory layers if desired for the
            historical log directories and files.
        **kwargs:  Additional keyword arguments, valid options are ``base_log_path`` and
            ``formatter``.

    Examples:
        >>> setup_logging('QE_LOGS', base_log_path='logs_dir')
        >>> import logging
        >>> logging.getLogger('Bubba Logger').critical('Urgent Message!')
        Writes files:
        logs_dir/QE_LOGS.master.log
            YYYY-MM-DD HH:MM:SS,FFF:CRITICAL:Bubba Logger             :Urgent Message!
        logs_dir/YYYY-MM-DD_HH_MM_SS.FFFFFF/QE_LOGS.master.log
            YYYY-MM-DD HH:MM:SS,FFF:CRITICAL:Bubba Logger             :Urgent Message!

        >>> setup_logging('QET', 'some_layer', 'another_layer', base_log_path='logs_dir')
        >>> import logging
        >>> logging.getLogger('SOME LOGGER').critical('LOOK AT ME')
        Writes files:
        logs_dir/QE_LOGS.master.log
            YYYY-MM-DD HH:MM:SS,FFF:CRITICAL:SOME LOGGER              :LOOK AT ME
        logs_dir/some_layer/another_layer/YYYY-MM-DD_HH_MM_SS.FFFFFF/QE_LOGS.master.log
            YYYY-MM-DD HH:MM:SS,FFF:CRITICAL:SOME LOGGER              :LOOK AT ME
    '''
    # The following two kwargs can be moved into the function call once python 2 support is ended.
    base_log_path = kwargs.get('base_log_path', DEFAULT_LOG_DIRECTORY)
    formatter = kwargs.get('formatter', logging.Formatter(DEFAULT_FORMATTER_STRING))

    root_log = logging.getLogger('')
    # If a FileHandler logger has not been added, create it now
    if not any(isinstance(x, logging.FileHandler) for x in root_log.handlers):
        ts_dir = '{:%Y%m%d_%H%M%S}'.format(datetime.now())
        ts_log_path = os.path.join(*((base_log_path,) + historical_log_dir_layers + (ts_dir,)))
        for dir_ in (ts_log_path, base_log_path):
            if not os.path.exists(dir_):
                os.makedirs(dir_)
            # Set up handler with encoding and msg formatter in log directory
            # Set mode to 'w' so that the known file name log file is reset.
            # Old logs still available in the timestamped directories.
            log_handler = logging.FileHandler(
                os.path.join(dir_, '{}.master.log'.format(log_name_prefix.lower())),
                mode='w',
                encoding='UTF-8'
            )
            log_handler.setFormatter(formatter)
            root_log.addHandler(log_handler)
