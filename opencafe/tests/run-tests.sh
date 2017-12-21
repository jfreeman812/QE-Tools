#! /bin/bash

# SUPER DRAFTY VERSION OF THIS SCRIPT!

# NOTE as of 2017-12-21:
#      This script assumes you already have OpenCAFE installed and configured!
#      Follow on work will make this "more" stand-alone, but we have to start somewhere.

# NOTE as of 2017-12-21:
#      This script assumes you are running it from the opencafe/tests directory.

export PYTHONPATH=../..

echo "First, a good run:"
cafe-parallel test opencafe.tests.test_decorators "$@"

echo "next, a bad run:"
cafe-parallel test opencafe.tests.bad_decorators "$@"
