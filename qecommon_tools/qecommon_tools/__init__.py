import itertools as _itertools
import os as _os
import string as _string


def _name_from_file(root, category):
    'Given root and category, return the contents of display_name.txt if it exists'
    name_path = _os.path.join(root, category, 'display_name.txt')
    if _os.path.exists(name_path):
        with open(name_path, 'r') as name_fo:
            return name_fo.read().rstrip('\r\n')


def display_name(root, category, category_name=None):
    '''
    Determine the display name for a category, given a root path and optional category name. If a
    file named display_name.txt is found in the root folder, use that for the display name.
    Otherwise, return a title-cased string from either category or category_name (if provided)
    '''
    name_from_file = _name_from_file(root, category)
    if name_from_file:
        return name_from_file

    if category_name:
        category = category_name.split('.')[-1]
    return _string.capwords(category.replace('_', ' '))


def padded_list(iterable, size, padding=None):
    '''
    Generate a list from the provided `iterable` at a fixed length (size), padding with `padding`
    if the original iterable is unsufficiently long
    '''
    return list(_itertools.islice(_itertools.chain(iterable, _itertools.repeat(padding)), size))
