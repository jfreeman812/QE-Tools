from datetime import date
from itertools import product
import os
import logging
import shutil
from tempfile import mkdtemp

import pytest
import qe_logging


LOG_MESSAGES = ['TEST LOG MESSAGE', 'ANOTHER IMPORTANT MESSAGE']
FILE_NAMES_TO_TEST = ['qe', '1234']
LOG_DIRS_TO_TEST = [
    mkdtemp(), 'logs_test', mkdtemp(dir=os.getcwd()), qe_logging.DEFAULT_LOG_DIRECTORY
]
DIR_LAYERS_TO_TEST = [[], ['abc'], ['def', 'ghij', 'zzzzz']]


@pytest.fixture(scope='function', params=LOG_DIRS_TO_TEST)
def log_dir(request):
    yield request.param
    if os.path.exists(request.param):
        shutil.rmtree(request.param)


def teardown_function():
    # Handlers must be cleared or they will cause interference with other tests.
    logging.getLogger('').handlers.clear()


def _find_first_match_with_prefix(dir_with_file, file_prefix):
    for file_name in os.listdir(dir_with_file):
        if file_name.startswith(file_prefix):
            return file_name
    return ''


def _get_historical_dir(*dir_layers):
    # Note as the format of the historical dir layers are subject to change, we will only check
    # that the dir starts with the year, as this should be fairly stable.
    return _find_first_match_with_prefix(os.path.join(*dir_layers), '{:%Y}'.format(date.today()))


def _get_file_contents(*paths):
    with open(os.path.join(os.path.join(*paths)), 'r') as f:
        return f.read()


@pytest.mark.parametrize('log_name_prefix', FILE_NAMES_TO_TEST)
def test_log_directory_is_created(log_dir, log_name_prefix):
    qe_logging.setup_logging(log_name_prefix, log_directory=log_dir)

    msg = 'Setup Logging Failed to create base directory {}'.format(log_dir)
    assert os.path.exists(log_dir), msg


@pytest.mark.parametrize('log_layers', DIR_LAYERS_TO_TEST)
def test_optional_dir_layers_are_created(log_dir, log_layers):
    qe_logging.setup_logging('', *log_layers, log_directory=log_dir)

    dir_layers = os.path.join(log_dir, *log_layers)
    msg = 'Setup Logging Failed to create optional directory layers {}'.format(dir_layers)
    assert os.path.exists(dir_layers), msg


@pytest.mark.parametrize('log_layers', DIR_LAYERS_TO_TEST)
def test_historical_dir_layers_are_created(log_dir, log_layers):
    qe_logging.setup_logging('', *log_layers, log_directory=log_dir)

    historical_dir = _get_historical_dir(log_dir, *log_layers)
    assert historical_dir, 'Setup Logging Failed to create historical Directory'


@pytest.mark.parametrize(
    'message,log_name_prefix,log_layers',
    product(LOG_MESSAGES, FILE_NAMES_TO_TEST, DIR_LAYERS_TO_TEST)
)
def test_log_files_contain_data(log_dir, message, log_name_prefix, log_layers):
    qe_logging.setup_logging(log_name_prefix, *log_layers, log_directory=log_dir)
    logging.critical(message)
    log_file_name = _find_first_match_with_prefix(log_dir, log_name_prefix)

    base_file_txt = _get_file_contents(log_dir, log_file_name)
    msg = '{} not found in log file, actual contents {}'.format(message, base_file_txt)
    assert message in base_file_txt, msg

    dir_layers = os.path.join(log_dir, *log_layers)
    historical_txt = _get_file_contents(dir_layers, _get_historical_dir(dir_layers), log_file_name)
    msg = '{} not found in historical file, actual contents {}'.format(message, historical_txt)
    assert message in historical_txt, msg
