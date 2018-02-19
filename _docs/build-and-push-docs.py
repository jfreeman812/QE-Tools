#! /usr/bin/env python
import os
import subprocess
import sys


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
subprocess.call(['{}/build-docs.py'.format(BASE_DIR)] + sys.argv[1:])
subprocess.call(['ghp-import', '-p', 'docs/'])
