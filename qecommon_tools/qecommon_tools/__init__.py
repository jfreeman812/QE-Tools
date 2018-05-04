from __future__ import print_function
from collections import Iterable
import itertools as _itertools
import os as _os
import random
import shutil as _shutil
import string as _string
import subprocess as _subprocess
import sys as _sys


def display_name(path, package_name=''):
    '''
    Create a human-readable name for a given project.

    Determine the display name for a project given a path and (optional) package name. If a
    display_name.txt file is found, the first line is returned. Otherwise, return a title-cased
    string from either the base directory or package_name (if provided)

    Args:
        path (str): Path for searching
        package_name (str): Sphinx-style, dot-delimited package name (optional)

    Returns:
        str: A display name for the provided path
    '''
    name_path = _os.path.join(path, 'display_name.txt')
    if _os.path.exists(name_path):
        with open(name_path, 'r') as name_fo:
            return name_fo.readline().rstrip('\r\n')
    raw_name = package_name.split('.')[-1] if package_name else _os.path.basename(path)
    return _string.capwords(raw_name.replace('_', ' '))


def format_if(format_str, content):
    '''
    Return a message string with formatted value if any content value is present.

    Useful for error-checking scenarios where you want a prepared error message
    if failures are present (passed in via content), or no message if no failures.

    Args:
        format_str (str): A message string with a single format brace to be filled
        content (str): A value to be filled into the format_str if present

    Returns:
        str: either the format_str with content included if content present,
             or an empty string if no content.
    '''
    return format_str.format(content) if content else ''


def padded_list(iterable, size, padding=None):
    '''
    Genereate a fixed-length list from an iterable, padding as needed.

    Args:
        iterable (iterable): Any iterable that needs padding
        size (int): The length for the returned list
        padding: Any value that should be used to pad an iterable that is too short

    Returns:
        list: The iterable parameter converted to a list, up to size, padded as needed.
    '''
    return list(_itertools.islice(_itertools.chain(iterable, _itertools.repeat(padding)), size))


def list_from(item):
    '''
    Generate a list from a single item or an iterable.

    Any item that is "false-y", will result in an empty list. Strings and dictionaries will be
    treated as single items, and not iterable.

    Args:
        item: A single item or an iterable.

    Examples:
        >>> list_from(None)
        []
        >>> list_from('abcd')
        ['abcd']
        >>> list_from(1234)
        [1234]
        >>> list_from({'abcd': 1234})
        [{'abcd': 1234}]
        >>> list_from(['abcd', 1234])
        ['abcd', 1234]
        >>> list_from({'abcd', 1234})
        ['abcd', 1234]
    '''
    if not item:
        return []
    if isinstance(item, (str, dict)) or not isinstance(item, Iterable):
        return [item]
    return list(item)


def cleanup_and_exit(dir_name=None, status=0, message=None):
    '''
    Cleanup a directory tree that was created and exit.

    Args:
        dir_name (string): Full path to a directory to remove (optional)
        status (int): Exit code to use for exit (optional)
        message (string): Message to print to standard error (optional)
    '''
    if dir_name:
        _shutil.rmtree(dir_name)
    exit(status=status, message=message)


def safe_run(commands, cwd=None):
    '''
    Run the given list of commands, only return if no error.

    If there is an error in attempting or actually running the commands
    error messages are printed on stdout and sys.exit will be called.
    '''

    try:
        status = _subprocess.call(commands, cwd=cwd)
    except OSError as e:
        print('')
        print('Error when trying to execute: "{}"'.format(' '.join(commands)))
        print('')
        print(e)
        _sys.exit(-1)

    if status:
        print('')
        print('Error {} from running: "{}"'.format(status, ' '.join(commands)))
        print('')
        _sys.exit(status)


def exit(status=0, message=None):
    '''
    Exit the program and optionally print a message to standard error.

    Args:
        status (int): Exit code to use for exit (optional)
        message (string): Message to print to standard error (optional)
    '''
    if message:
        print(message, file=_sys.stderr)
    _sys.exit(status)


def error_if(check, status=None, message=''):
    '''
    Exit the program if a provided check is true.

    Exit the program if the check is true. If a status is provided, that code is used for the
    exit code; otherwise the value from check is used. An optional message for standard error can
    also be provided

    Args:
        check: Anything with truthiness that can determine if the program should exit or not
        status (int): Exit code to use for exit (optional)
        message (string): Message to print to standard error if check is True (optional)
    '''
    if check:
        exit(status=status or check, message=message.format(check))


def dict_strip_value(dict_, value=None):
    '''
    Return a new dict based on stripping out any key with the given value.
    NOTE: The default value 'None' is chosen because it is a common case.
    Unlike other functions, value 'None' is literally the value None.

    Args:
        dict_ (dict): A dictionary to strip values from.
        value: Any value that should be stripped from the dictionary.

    Returns:
        dict: A new dictionary without the offending keys or values.
    '''
    return {k: v for k, v in dict_.items() if v != value}


def generate_random_string(prefix='', suffix='', size=8):
    '''
    Generate a random string of the specified size.

    Examples:
        > generate_random_string()
        vng345jn
        > generate_random_string(prefix='Lbs-', suffix='-test', size=15)
        Lbs-js7eh9-test
        > generate_random_string(prefix='Lbs-', size=15)
        Lbs-js7eh98sfnk
        > generate_random_string(suffix='-test', size=15)
        8sdfjs7eh9-test

    Args:
        prefix (str): The string to prepend to the beginning of the random string. (optional)
        suffix (str): The string to append to the end of the random string. (optional)
        size (int): The number of characters the random string should have. (defaults to 8)

    Returns:
        str: A randomly generated string.

    Raises:
        AssertionError: if the specified length is incompatible with prefix/suffix length
    '''
    possible_characters = _string.ascii_lowercase + _string.digits
    rand_string_length = size - len(prefix) - len(suffix)
    message = '"size" of {} too short with prefix {} and suffix {}!'
    assert rand_string_length > 0, message.format(size, prefix, suffix)
    rand_string = ''.join(random.choice(possible_characters) for _ in range(rand_string_length))
    return '{}{}{}'.format(prefix, rand_string, suffix)


def must_get_key(a_dict, key):
    '''
    Either return the value for the key, or raise an exception.

    The exception will indicate what the valid keys are.
    Inspired by Gherkin steps so that a typo in the Gherkin
    will result in a more helpful error message than the stock KeyError.

    Args:
        a_dict (dict): Dictionary with the values
        key (str): The key whose value is desired

    Returns:
        The value found on the key

    Raises:
        KeyError: if the given key is not present in the dictionary.
    '''
    if key not in a_dict:
        raise KeyError(
            '{} is not one of: {}'.format(key, ', '.join(sorted(map(str, a_dict))))
        )
    return a_dict[key]


def must_get_keys(a_dict, *keys):
    '''
    Either return the value found for the keys provided, or raise an exception.

    Args:
        a_dict (dict): Dictionary with the values
        keys (str): The key or keys whose value is desired

    Returns:
        The value found on the final key

    Raises:
        KeyError: if any of the given keys are not present in the dictionary.
    '''
    for key in keys:
        a_dict = must_get_key(a_dict, key)
    return a_dict


def var_from_env(var_name):
    '''
    Get an environment variable and raise an error if it is not set or has an empty value.

    Raises:
        ValueError: if the variable name is not set or has an empty value.
    '''
    envvar = _os.environ.get(var_name)
    if not envvar:
        raise ValueError('"{}" variable not found!'.format(var_name))
    return envvar
