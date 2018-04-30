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
        **kwargs:  Additional keyword arguments, valid options are ``base_log_dir`` and
            ``formatter``.

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

    # Only add our own FileHandler loggers if none are already present.
    if any(isinstance(x, logging.FileHandler) for x in root_log.handlers):
        return

    timestamp = '{:%Y%m%d_%H%M%S}'.format(datetime.now())
    timestamp_log_dir = os.path.join(*((base_log_dir,) + historical_log_dir_layers + (timestamp,)))
    master_log_filename = '{}.master.log'.format(log_name_prefix.lower())
    for dir_ in (timestamp_log_dir, base_log_dir):
        if not os.path.exists(dir_):
            os.makedirs(dir_)

        # Set mode to 'w' so that any known file name log file is reset.
        # Previous logs will still be available in their timestamped directories.
        log_handler = logging.FileHandler(
            os.path.join(dir_, master_log_filename),
            mode='w',
            encoding='UTF-8'
        )
        log_handler.setFormatter(formatter)
        root_log.addHandler(log_handler)
