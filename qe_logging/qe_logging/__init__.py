import logging
import os
from datetime import datetime


DEFAULT_LOG_DIRECTORY = 'logs'


def setup_logging(log_name_prefix, *historical_log_dir_layers, log_directory=DEFAULT_LOG_DIRECTORY,
                  formatter=None):
    '''
    Will setup logging file handlers with a standard format for QE logging.

    One handler will be set to write in the base log directory, the other in the historical log dir
    layers (if provided) with time stamped directories.

    Args:
        log_name_prefix (str): The prefix for the log file name, prepended to .master.log.
        *historical_log_dir_layers (str):   Additional directory layers if desired for the
            historical log directories and files.
        log_directory: (str) - The directory for the logs.
        formatter (logging.Formatter): A logging formatter to use in the file handlers, if not
            provided will default to the standard QE logging formatter.

    Examples:
        >>> setup_logging('QE_LOGS', log_directory='logs_dir')
        >>> import logging
        >>> logging.getLogger('Bubba Logger').critical('Urgent Message!')
        Writes files:
        logs_dir/QE_LOGS.master.log
            YYYY-MM-DD HH:MM:SS,FFF:CRITICAL:Bubba Logger             :Urgent Message!
        logs_dir/YYYY-MM-DD_HH_MM_SS.FFFFFF/QE_LOGS.master.log
            YYYY-MM-DD HH:MM:SS,FFF:CRITICAL:Bubba Logger             :Urgent Message!

        >>> setup_logging('QET', 'some_layer', 'another_layer', log_directory='logs_dir')
        >>> import logging
        >>> logging.getLogger('SOME LOGGER').critical('LOOK AT ME')
        Writes files:
        logs_dir/QE_LOGS.master.log
            YYYY-MM-DD HH:MM:SS,FFF:CRITICAL:SOME LOGGER              :LOOK AT ME
        logs_dir/some_layer/another_layer/YYYY-MM-DD_HH_MM_SS.FFFFFF/QE_LOGS.master.log
            YYYY-MM-DD HH:MM:SS,FFF:CRITICAL:SOME LOGGER              :LOOK AT ME
    '''
    root_log = logging.getLogger('')
    # If a FileHandler logger has not been added, create it now
    if not any(isinstance(x, logging.FileHandler) for x in root_log.handlers):
        ts_dir = str(datetime.now()).replace(' ', '_').replace(':', '_')
        log_dir = os.path.join(*[log_directory, *historical_log_dir_layers, ts_dir])
        if not formatter:
            formatter = logging.Formatter('{asctime}:{levelname:8}:{name:25}:{message}', style='{')
        for dir_ in (log_dir, log_directory):
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
