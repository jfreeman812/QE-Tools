from __future__ import print_function
import itertools as _itertools
import os as _os
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


def must_get_key(a_dict, key):
    '''
    Either return the value for the key, or raise an exception.
    The exception will indicate what the valid keys are.
    Inspired by Gherkin steps so that a typo in the Gherkin
    will result in a more helpful error message than the stock KeyError.
    '''
    if key not in a_dict:
        raise KeyError(
            '{} is not one of: {}'.format(key, ', '.join(sorted(map(str, a_dict))))
        )
    return a_dict[key]


def must_get_keys(a_dict, *keys):
    '''
    Either return the value found for they keys provided, or raise an exception with a useful error
    message if any of the keys are not found.
    :param a_dict (dct): The dictionary with the values.
    :param keys (str): One or many keys to get the values for.
    :return: The value found in the dictionary.
    '''
    for key in keys:
        a_dict = must_get_key(a_dict, key)
    return a_dict
