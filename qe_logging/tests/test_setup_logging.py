from datetime import date
from itertools import product
import os
import logging
import shutil
import subprocess
from tempfile import mkdtemp
from uuid import uuid4

import pytest
import qe_logging


LOG_MESSAGES = ['TEST LOG MESSAGE', 'ANOTHER IMPORTANT MESSAGE']
FILE_NAMES_TO_TEST = ['qe', '1234']
LOG_DIRS_TO_TEST = [mkdtemp(), mkdtemp(dir=os.getcwd()), str(uuid4())]
DIR_LAYERS_TO_TEST = [[], ['abc'], ['def', 'ghij', 'zzzzz']]


@pytest.fixture(scope='function', params=LOG_DIRS_TO_TEST)
def log_dir(request):
    yield request.param
    if os.path.exists(request.param):
        shutil.rmtree(request.param)


def teardown_function():
    # Handlers must be cleared or they will cause interference with other tests.
    del logging.getLogger('').handlers[:]


def _get_file_contents(*paths):
    with open(os.path.join(os.path.join(*paths)), 'r') as f:
        return f.read()


@pytest.mark.parametrize('log_name_prefix', FILE_NAMES_TO_TEST)
def test_log_directory_is_created(log_dir, log_name_prefix):
    qe_logging.setup_logging(log_name_prefix, base_log_dir=log_dir)

    msg = 'Setup Logging Failed to create base directory {}'.format(log_dir)
    assert os.path.exists(log_dir), msg


@pytest.mark.parametrize('log_layers', DIR_LAYERS_TO_TEST)
def test_log_files_are_created(log_dir, log_layers):
    log_filenames = qe_logging.setup_logging('', *log_layers, base_log_dir=log_dir)

    expected_log_filename_count = 2
    assert_msg = 'Setup Logging failed to create {} log files: {}'.format(
        expected_log_filename_count, log_filenames)
    assert len(log_filenames) == expected_log_filename_count, assert_msg

    for log_filename in log_filenames:
        existance_assert_msg = 'Setup Logging Failed to create log file {!r}'.format(log_filename)
        assert os.path.exists(log_filename), existance_assert_msg


@pytest.mark.parametrize(
    'message,log_name_prefix,log_layers',
    product(LOG_MESSAGES, FILE_NAMES_TO_TEST, DIR_LAYERS_TO_TEST)
)
def test_log_files_contain_data(log_dir, message, log_name_prefix, log_layers):
    log_filenames = qe_logging.setup_logging(log_name_prefix, *log_layers, base_log_dir=log_dir)
    logging.critical(message)

    for log_filename in log_filenames:
        file_contents = _get_file_contents(log_filename)
        msg = '{} not found in log file {}, actual contents {}'.format(
            message, log_filename, file_contents)
        assert message in file_contents, msg


def test_unconfigured_logging_generates_output():
    output = subprocess.check_output(['qe_logging/tests/no_log_test.py'], stderr=subprocess.STDOUT)
    assert output, 'Expected logging out with no configuration setup at all'


def test_unconfigured_logging_can_be_suppressed():
    new_env = os.environ.copy()
    new_env['NO_LOG'] = 'Arbitrary_value'  # Tell test helper script to shut off it's logging.
    output = subprocess.check_output(['qe_logging/tests/no_log_test.py'],
                                     stderr=subprocess.STDOUT,
                                     env=new_env)
    assert not output, 'Unexpected output when logging suppressed'
