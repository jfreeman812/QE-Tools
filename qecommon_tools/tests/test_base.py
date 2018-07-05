'''Unit tests for the qecommon_tools tools.'''

from itertools import product
import tempfile
from uuid import uuid4
from os import path, mkdir
import random
import string

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


DICT_STRIP_VALUES = ['', None, 'None', 1234, []]
DIST_STRIP_CASES = [({uuid4(): x for x in DICT_STRIP_VALUES}, y) for y in DICT_STRIP_VALUES]


@pytest.mark.parametrize('dict_to_strip,value_to_strip', DIST_STRIP_CASES)
def test_dict_strip_valid_values_remain(dict_to_strip, value_to_strip):
    stripped_dictionary = qecommon_tools.dict_strip_value(dict_to_strip, value=value_to_strip)
    for valid_value in [x for x in DICT_STRIP_VALUES if x != value_to_strip]:
        assert valid_value in stripped_dictionary.values()


@pytest.mark.parametrize('dict_to_strip,value_to_strip', DIST_STRIP_CASES)
def test_dict_strip_stripped_values_are_gone(dict_to_strip, value_to_strip):
    stripped_dictionary = qecommon_tools.dict_strip_value(dict_to_strip, value=value_to_strip)
    assert value_to_strip not in stripped_dictionary.values()


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


def test_no_virtual_env(monkeypatch):
    # Don't depend on tests being run in, or not run in, a virtual environment.
    monkeypatch.delenv('VIRTUAL_ENV', raising=False)
    arbitrary_exit_code = 45
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        qecommon_tools.must_be_in_virtual_environment(exit_code=arbitrary_exit_code)
    assert pytest_wrapped_e.value.code == arbitrary_exit_code


def test_virtual_env(monkeypatch):
    # Don't depend on tests being run in, or not run in, a virtual environment.
    monkeypatch.setenv('VIRTUAL_ENV', 'arbitrary_value')
    arbitrary_exit_code = 45
    # If this next function call exits, pytest will report an error:
    qecommon_tools.must_be_in_virtual_environment(exit_code=arbitrary_exit_code)


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


def test_random_string_length():
    text = qecommon_tools.generate_random_string(size=8)
    assert len(text) == 8


def test_random_string_prefix():
    prefix = 'test-'
    text = qecommon_tools.generate_random_string(prefix=prefix, size=8)
    assert len(text) == 8
    assert text.startswith(prefix)


def test_random_string_suffix():
    suffix = '-test'
    text = qecommon_tools.generate_random_string(suffix=suffix, size=8)
    assert len(text) == 8
    assert text.endswith(suffix)


def test_string_size_failure():
    with pytest.raises(AssertionError):
        qecommon_tools.generate_random_string(
            prefix='this-is-a-long-prefix-',
            suffix='-this-is-a-long-suffix',
            size=3
        )


KEY_TEST_DICT = {'a': 1, 1: 'a', 'key': 'value', 'nested': {'a': 5}}


def _sorted_key_names(dict_):
    return sorted(map(str, dict_))


def test_valid_key():
    key = random.choice(list(KEY_TEST_DICT.keys()))
    value = qecommon_tools.must_get_key(KEY_TEST_DICT, key)
    assert value == KEY_TEST_DICT[key]


def test_invalid_key():
    key = qecommon_tools.generate_random_string()
    expected_msg = '{} is not one of: {}'.format(key, _sorted_key_names(KEY_TEST_DICT))
    with pytest.raises(KeyError, message=expected_msg):
        qecommon_tools.must_get_key(KEY_TEST_DICT, key)


def test_valid_keys():
    value = qecommon_tools.must_get_keys(KEY_TEST_DICT, 'nested', 'a')
    assert value == KEY_TEST_DICT['nested']['a']


def test_invalid_keys():
    key = qecommon_tools.generate_random_string()
    expected_msg = '{} is not one of: {}'.format(key, _sorted_key_names(KEY_TEST_DICT['nested']))
    with pytest.raises(KeyError, message=expected_msg):
        qecommon_tools.must_get_keys(KEY_TEST_DICT, 'nested', key)


FORMAT_STR = 'Test format string: {}'


def test_format_if_with_content():
    value = 'test value'
    assert qecommon_tools.format_if(FORMAT_STR, value) == FORMAT_STR.format(value)


def test_format_if_no_content():
    value = None
    assert qecommon_tools.format_if(FORMAT_STR, value) == ''


FALSEY_VALUES = [None, '', [], {}, False, 0]
SINGLE_ITEM_VALUES = [1, 11111, '1', 'ABCDEFG', u'ABCDEFG', [[]], {'A': 1, 'B': 2}, True]
ITERABLE_VALUES = [[1, 2, 3], list('abcde'), [[1], [2], [3]], map(lambda x: x, [1, 2, 3]), {1, 2}]


@pytest.mark.parametrize('falsey_items', FALSEY_VALUES)
def test_list_from_empty_values(falsey_items):
    assert qecommon_tools.list_from(falsey_items) == []


@pytest.mark.parametrize('single_items', SINGLE_ITEM_VALUES)
def test_list_from_single_items(single_items):
    assert len(qecommon_tools.list_from(single_items)) == 1


@pytest.mark.parametrize('iterable_items', ITERABLE_VALUES)
def test_list_from_iterable(iterable_items):
    results = qecommon_tools.list_from(iterable_items)
    assert len(results) > 1
    for item in iterable_items:
        assert item in results


def test_get_file_contents(temp_dir):
    file_path = path.join(temp_dir, 'test.txt')
    with open(file_path, 'w') as f:
        f.write(TEST_MESSAGE)
    assert qecommon_tools.get_file_contents(file_path) == TEST_MESSAGE


def test_get_file_docstring():
    assert qecommon_tools.get_file_docstring(__file__) == __doc__


def _is_vowel(value):
    return value.lower() in ['a', 'e', 'i', 'o', 'u']


FILTER_LINES_DATA = [
    # (input, expected_output, line_filter, output)
    ('A\nB\nC\nD\nE', 'A\nE', _is_vowel, None),  # str -> str
    ('A\nB\nC\nD\nE', ['A', 'E'], _is_vowel, list),  # str -> list
    (['A', 'B', 'C', 'D', 'E'], ['A', 'E'], _is_vowel, None),  # list -> list
    (['A', 'B', 'C', 'D', 'E'], 'A\nE', _is_vowel, str),  # list -> str
]


@pytest.mark.parametrize('input_,expected_output,line_filter,return_type', FILTER_LINES_DATA)
def test_filter_lines_given_str(input_, expected_output, line_filter, return_type):
    output = qecommon_tools.filter_lines(line_filter, input_, return_type)
    assert output == expected_output


STRING_TO_LIST_DATA = {
    '  This is a simple space separated list':
        {'kwargs': {'sep': None},
         'results': ['This', 'is', 'a', 'simple', 'space', 'separated', 'list'],
         },
    ' Sample value, from, a, config, file ':
        {'kwargs': {},
         'results': ['Sample value', 'from', 'a', 'config', 'file'],
         },
    ' plus-separated+string+here':
        {'kwargs': {'sep': '+'},
         'results': ['plus-separated', 'string', 'here'],
         },
    ' -strike-through-=-another-=-word-,=blah== ':
        {'kwargs': {'sep': '=', 'maxsplit': 2, 'chars': '-'},
         'results': [' -strike-through', 'another', 'word-,=blah== '],
         },
}


@pytest.mark.parametrize('source,test_data', STRING_TO_LIST_DATA.items())
def test_string_to_list(source, test_data):
    assert qecommon_tools.string_to_list(source, **test_data['kwargs']) == test_data['results']


def test_fib_or_max():
    # All numbers chosen here are arbitrary
    assert qecommon_tools.fib_or_max(0, 30) == 0
    assert qecommon_tools.fib_or_max(6, 30) == 8
    assert qecommon_tools.fib_or_max(1000, 30) == 30


def make_retry_helper(retry_count, exceptions_to_catch, max_retry_sleep):
    @qecommon_tools.retry_on_exceptions(retry_count, exceptions_to_catch, max_retry_sleep)
    def function_that_might_throw(exception, counter_list_hack):
        counter_list_hack[0] += 1
        if exception:
            raise exception

    return function_that_might_throw


def test_retry_on_exception():
    # All these are arbitrary, but...
    # keep the retry count and sleep time low so tests don't take too long to run.
    retry_count = 3
    helper_that_might_throw = make_retry_helper(retry_count, (KeyError, NameError), 2)

    # No exception, should only be called once.
    counter = [0]
    helper_that_might_throw(None, counter)
    assert counter[0] == 1

    # uncaught exception, should only be called once.
    arbitrary_exception = IndexError   # Anything not listed above...
    counter = [0]
    with pytest.raises(IndexError):
        helper_that_might_throw(IndexError, counter)
    assert counter[0] == 1

    # caught exceptions, make sure retry count is correct.
    counter = [0]
    arbitrary_exception = KeyError
    with pytest.raises(arbitrary_exception):
        helper_that_might_throw(arbitrary_exception, counter)

    # <n> retries means <n>+1 calls
    assert counter[0] == retry_count + 1


def test_retry_on_exception_error_handling():
    with pytest.raises(AssertionError) as e:
        make_retry_helper(10, None, 1)
    # Make sure we get the right error, but don't lock down the exact error string raised.
    assert 'No exception' in str(e)

    with pytest.raises(AssertionError) as e:
        make_retry_helper(0, KeyError, 1)
    # Make sure we get the right error, but don't lock down the exact error string raised.
    assert 'max_retry_count must be' in str(e)


def test_only_item_of():
    bad_lists = [[], list(range(100))]
    for bad_list in bad_lists:
        with pytest.raises(AssertionError):
            qecommon_tools.only_item_of(bad_list)

    assert qecommon_tools.only_item_of([1]) == 1


def test_simple_responseinfo_data():
    response = qecommon_tools.generate_random_string()
    description = qecommon_tools.generate_random_string()
    extra_field = qecommon_tools.generate_random_string()
    a_response = qecommon_tools.ResponseInfo(response=response, description=description,
                                             extra_field=extra_field)
    assert a_response.response == response
    assert a_response.description == description
    assert a_response.extra_field == extra_field
    # No callbacks, so the response data should just be the response
    assert a_response.response_data == response


# Testing helpers for the ResponseInfo callback mechanism.

# Keep track of how many times the callback has been invoked.
# Using the usual list hack to avoid global variable declarations and annoyances.
arbitrary_callback_counter = [0]

ARBITRARY_CALLBACK_VALUE = 'phone number 867-5329'


@pytest.fixture
def random_string():
    '''Something arbitrary and random that doesn't collide with ARBITRARY_CALLBACK_VALUE'''
    # making the value larger ensures it won't collide.
    return qecommon_tools.generate_random_string(size=len(ARBITRARY_CALLBACK_VALUE) + 1)


def arbitrary_callback():
    arbitrary_callback_counter[0] += 1
    return ARBITRARY_CALLBACK_VALUE


def test_callback_response_data(random_string):
    a_response = qecommon_tools.ResponseInfo(response=random_string,
                                             response_callback=arbitrary_callback)
    assert a_response.response_data == ARBITRARY_CALLBACK_VALUE

    # Now make sure .response has been changed:
    assert a_response.response == ARBITRARY_CALLBACK_VALUE


def test_callback_response_data_callback_only_called_once():
    a_response = qecommon_tools.ResponseInfo(response_callback=arbitrary_callback)

    arbitrary_callback_counter[0] = 0
    a_response.run_response_callback()

    assert a_response.response == ARBITRARY_CALLBACK_VALUE
    assert arbitrary_callback_counter[0] == 1

    a_response.run_response_callback()
    assert a_response.response == ARBITRARY_CALLBACK_VALUE
    assert arbitrary_callback_counter[0] == 1


def test_extract_response_data():
    arbitrary_string = 'arbitrary_string'.lower()
    a_response = qecommon_tools.ResponseInfo(response=arbitrary_string,
                                             response_data_extract=str.swapcase)
    assert a_response.response_data == arbitrary_string.swapcase()


def test_extract_and_callback_response_data(random_string):
    a_response = qecommon_tools.ResponseInfo(response=random_string,
                                             response_callback=arbitrary_callback,
                                             response_data_extract=str.swapcase)
    assert a_response.response_data == ARBITRARY_CALLBACK_VALUE.swapcase()


def test_empty_notemptylist_errors_out():
    with pytest.raises(AssertionError):
        for item in qecommon_tools.NotEmptyList():
            pass


def test_mundane_notemptylist():
    arbitrary_list_len = random.randint(1, 10)  # Anything > 0 is fine.
    my_list = qecommon_tools.NotEmptyList()
    my_list.extend(range(arbitrary_list_len))
    for item in my_list:
        pass   # make sure no exception thrown.
    assert my_list == list(range(arbitrary_list_len))


def test_commonattributelist_attr_access():
    arbitrary_list_len = random.randint(1, 10)  # Anything > 0 is fine.
    my_list = qecommon_tools.CommonAttributeList()
    for x in range(arbitrary_list_len):
        my_list.append(qecommon_tools.ResponseInfo(data=x))
    assert my_list.data == list(range(arbitrary_list_len))


def test_commonattributelist_attr_set(random_string):
    arbitrary_list_len = random.randint(1, 10)  # Anything > 0 is fine.
    my_list = qecommon_tools.CommonAttributeList()

    # First set up different data for each item
    for x in range(arbitrary_list_len):
        my_list.append(qecommon_tools.ResponseInfo(data=x))

    # overwrite data with the same value.
    my_list.data = random_string

    # make sure new value is consisten across each element.
    assert my_list.data == [random_string] * arbitrary_list_len


def test_commonattributelist_update_all(random_string):
    arbitrary_list_len = random.randint(1, 10)  # Anything > 0 is fine.
    my_list = qecommon_tools.CommonAttributeList()

    # First set up different data for each item
    for x in range(arbitrary_list_len):
        my_list.append(qecommon_tools.ResponseInfo(data=x))

    my_list.update_all(data=random_string, data2=random_string + random_string)

    # make sure new values are consisten across each element.
    assert my_list.data == [random_string] * arbitrary_list_len
    assert my_list.data2 == [random_string + random_string] * arbitrary_list_len


def test_responselist_set():
    arbitrary_list_len = random.randint(1, 10)  # Anything > 0 is fine.
    my_list = qecommon_tools.ResponseList()
    my_list.extend(range(arbitrary_list_len))
    assert len(my_list) == arbitrary_list_len
    my_list.set([])
    assert len(my_list) == 0
    my_list.set([-1, -2])
    assert len(my_list) == 2
    assert my_list == [-1, -2]


def test_responselist_single_item():
    my_list = qecommon_tools.ResponseList()
    with pytest.raises(AssertionError):
        my_list.single_item

    my_list.append(3)
    assert my_list.single_item == 3

    my_list.append(4)
    with pytest.raises(AssertionError):
        my_list.single_item


def test_response_list_build_and_set(random_string):
    response_list = qecommon_tools.ResponseList()

    assert len(response_list) == 0
    response_list.build_and_set(response=random_string)
    assert len(response_list) == 1
    assert isinstance(response_list.single_item, qecommon_tools.ResponseInfo)


def test_response_list_run_response_callbacks():
    arbitrary_list_len = random.randint(1, 10)  # Anything > 0 is fine.
    response_list = qecommon_tools.ResponseList()

    response_list.extend(qecommon_tools.ResponseInfo(response_callback=arbitrary_callback)
                         for x in range(arbitrary_list_len))
    arbitrary_callback_counter[0] = 0
    response_list.run_response_callbacks()
    assert arbitrary_callback_counter[0] == arbitrary_list_len
