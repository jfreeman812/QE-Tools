import itertools as _itertools
import os as _os
import string as _string


def _name_from_file(root, category):
    name_path = _os.path.join(root, category, 'display_name.txt')
    if _os.path.exists(name_path):
        with open(name_path, 'r') as name_fo:
            return name_fo.read().rstrip('\r\n')


def display_name(root, category, category_name=None):
    name_from_file = _name_from_file(root, category)
    if name_from_file:
        return name_from_file

    if category_name:
        category = category_name.split('.')[-1]
    return _string.capwords(category.replace('_', ' '))


def padded_list(iterable, size, padding=None):
    return list(_itertools.islice(_itertools.chain(iterable, _itertools.repeat(padding)), size))
