from itertools import chain, repeat, islice
import os
import string


def _name_from_file(root, category):
    name_path = os.path.join(root, category, 'display_name.txt')
    if os.path.exists(name_path):
        with open(name_path, 'r') as name_fo:
            return name_fo.read().rstrip('\r\n')


def display_name(root, category, category_name=None):
    name_from_file = _name_from_file(root, category)
    if name_from_file:
        return name_from_file

    if category_name:
        category = category_name.split('.')[-1]
    return string.capwords(category.replace('_', ' '))


def padded_list(iterable, size, padding=None):
    return list(islice(chain(iterable, repeat(padding)), size))
