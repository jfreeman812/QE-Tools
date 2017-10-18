#!/usr/bin/env python

'''
A very simple script that will check over our "source" files to see if
there any lines which will fail Unicode->ASCII conversion which happens
as part of iterating over file lines.
'''

import os


def check_file(dir_path, file_name):
    full_path_file_name = os.path.join(dir_path, file_name)
    with open(full_path_file_name, 'r') as feature_file:
        last_line_number = 0
        try:
            for line_no, line in enumerate(feature_file, 1):
                last_line_number = line_no   # Otherwise line_no is not visible after the loop
        except UnicodeDecodeError as ude:
            print('While processing line {} of {}, got a unicode failure:'.format(
                last_line_number + 1, full_path_file_name))
            print(ude)
            print()


extensions_to_check = ['.feature', '.rb', '.py']


def should_check(file_name):
    return any(map(file_name.lower().endswith, extensions_to_check))


for dir_path, dir_names, file_names in os.walk(os.curdir):
    if '.git' in dir_names:
        dir_names.remove('.git')
    for file_name in filter(should_check, file_names):
        check_file(dir_path, file_name)
