import itertools as _itertools
import os as _os
import shutil as _shutil
import string as _string
import subprocess as _subprocess
import sys as _sys


def display_name(path, package_name=''):
    '''Create a human-readable name for a given project.

    Determine the display name for a project given a path and (optional) package name. If a
    display_name.txt file is found, the first line is returned. Oterwise, return a title-cased
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
    '''Genereate a fixed-length list from an iterable, padding as needed.

    Args:
        iterable (iterable): Any iterable that needs padding
        size (int): The length for the returned list
        padding: Any value that should be used to pad an iterable that is too short

    Returns:
        list: The iterable parameter converted to a list, up to size, padded as needed.
    '''
    return list(_itertools.islice(_itertools.chain(iterable, _itertools.repeat(padding)), size))


def cleanup_and_exit(dir_name=None):
    if dir_name:
        _shutil.rmtree(dir_name)
    _sys.exit(0)


def safe_run(commands):
    '''run the given list of commands, only return if no error.

    If there is an error in attempting or actually running the commands
    error messages are printed on stdout and sys.exit will be called.
    '''

    try:
        status = _subprocess.call(commands)
    except OSError as e:
        print('')
        print('Error trying to execute: {}'.format(' '.join(commands)))
        print('')
        print(e)
        _sys.exit(-1)

    if status:
        print('')
        print('Error trying to run: {}'.format(' '.join(commands)))
        print('')
        _sys.exit(status)

