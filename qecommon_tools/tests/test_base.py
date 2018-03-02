from itertools import product
import tempfile
from os import path, mkdir

import pytest
import qecommon_tools


TEST_MESSAGE = 'Test Message'


@pytest.fixture
def list_for_padding():
    '''Returns a short list to be used to pad into a longer list'''
    return ['a', 'b']


@pytest.fixture
def temp_dir():
    '''Creates and return a tmpdir for testing'''
    return tempfile.mkdtemp()


@pytest.fixture
def temp_dir_with_name_file():
    dir_path = tempfile.mkdtemp()
    with open(path.join(dir_path, 'display_name.txt'), 'w') as f:
        f.write(TEST_MESSAGE)
    return dir_path


PACKAGE_NAMES = {None: 'Test Directory', 'test.package.name_for_testing': 'Name For Testing'}


@pytest.mark.parametrize('package_name_and_expected', PACKAGE_NAMES.items())
def test_display_name_without_name_file(temp_dir, package_name_and_expected):
    package_name, expected = package_name_and_expected
    target_dir = path.join(temp_dir, 'test_directory')
    mkdir(target_dir)
    display_name = qecommon_tools.display_name(target_dir, package_name)
    assert display_name == expected


@pytest.mark.parametrize('package_name', PACKAGE_NAMES.keys())
def test_display_name_with_name_file(temp_dir_with_name_file, package_name):
    display_name = qecommon_tools.display_name(temp_dir_with_name_file, package_name)
    assert display_name == TEST_MESSAGE


PADDED_LIST_CASES = list(product([0, 5, 15], [None, 'TEST']))


@pytest.mark.parametrize('target_length,padding', PADDED_LIST_CASES)
def test_padding_length(list_for_padding, target_length, padding):
    padded = qecommon_tools.padded_list(list_for_padding, target_length, padding=padding)
    assert len(padded) == target_length


@pytest.mark.parametrize('target_length,padding', PADDED_LIST_CASES)
def test_padding_value(list_for_padding, target_length, padding):
    padded = qecommon_tools.padded_list(list_for_padding, target_length, padding=padding)
    assert padded.count(padding) == max(target_length - len(list_for_padding), 0)


def _cleanup_and_exit(dir_path=None):
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        qecommon_tools.cleanup_and_exit(dir_name=dir_path)
    assert pytest_wrapped_e.value.code == 0


def test_cleanup_and_exit_without_dir():
    _cleanup_and_exit()


def test_cleanup_and_exit_with_dir():
    dir_path = temp_dir()
    _cleanup_and_exit(dir_path=dir_path)
    assert not path.exists(dir_path)


def test_safe_run_passing():
    # This should not raise any exceptions (pytest will fail the test if it does)
    qecommon_tools.safe_run(['ls'])


@pytest.mark.parametrize('command,expected_exit_codes', [
    ('asdfadssfl', (-1,)),  # A nonexistent command will raise an OSError
    ('ls asdfsdfsfs', (1,  # Mac exit code
                       2  # Centos Exit code
                       ))  # A call to list a nonexistent directory will return a nonzero exit code
])
def test_safe_run_with_fail(command, expected_exit_codes):
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        qecommon_tools.safe_run(command.split())
    assert pytest_wrapped_e.value.code in expected_exit_codes


TEST_EXIT_CODES = [-1, 0, 1]


@pytest.mark.parametrize('exit_code', TEST_EXIT_CODES)
def test_exit_without_message(capsys, exit_code):
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        qecommon_tools.exit(status=exit_code)
    assert pytest_wrapped_e.value.code == exit_code


@pytest.mark.parametrize('exit_code', TEST_EXIT_CODES)
def test_exit_with_message(capsys, exit_code):
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        qecommon_tools.exit(status=exit_code, message=TEST_MESSAGE)
    assert pytest_wrapped_e.value.code == exit_code
    out, err = capsys.readouterr()
    assert TEST_MESSAGE in err


WITHOUT_CHECK_VALUES = list(product([None, '', 0], TEST_EXIT_CODES, ['', TEST_MESSAGE]))


@pytest.mark.parametrize('check,exit_code,message', WITHOUT_CHECK_VALUES)
def test_error_if_without_check(check, exit_code, message):
    qecommon_tools.error_if(check, status=exit_code, message=message)


WITH_CHECK_VALUES = list(product(['Error', 1, -1], TEST_EXIT_CODES, ['', TEST_MESSAGE]))


@pytest.mark.parametrize('check,exit_code,message', WITH_CHECK_VALUES)
def test_error_if_with_check(capsys, check, exit_code, message):
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        qecommon_tools.error_if(check, status=exit_code, message=message)
    out, err = capsys.readouterr()
    assert message in err
    assert pytest_wrapped_e.value.code == exit_code or check
