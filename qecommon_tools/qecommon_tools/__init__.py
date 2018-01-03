import itertools as _itertools
import os as _os
import string as _string


def display_name(path, package_name=''):
    '''Create a human-readable name for a given project.

    Determine the display name for a project given a path and (optional) package name. If a
    display_name.txt file if found, the first line is returned. Oterwise, return a title-cased
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
    '''Generate a list from the provided `iterable` at a fixed length (size), padding with `padding`
    if the original iterable is unsufficiently long

    Args:
        iterable (iterable): Any iterable that needs padding
        size (int): The length for the returned list
        padding: Any value that should be used to pad an iterable that is too short

    Returns:
        list: A list that has been padded or truncated as needed
    '''
    return list(_itertools.islice(_itertools.chain(iterable, _itertools.repeat(padding)), size))
