import os
import string


def _category_or_product_name_from_file(root, category):
    name_path = os.path.join(root, category, 'display_name.txt')
    if os.path.exists(name_path):
        with open(name_path, 'r') as name_fo:
            return name_fo.read().rstrip('\r\n')


def category_or_product_name(root, category_or_product, category_name=None):
    name_from_file = _category_or_product_name_from_file(root, category_or_product)
    if name_from_file:
        return name_from_file

    if category_name:
        category_or_product = category_name.split('.')[-1]
    return string.capwords(category_or_product.replace('_', ' '))
