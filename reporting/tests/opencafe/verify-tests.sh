#! /bin/bash

# Make sure that the basic machinery is all working,
# that the modules can be imported, and decorators function as expected.

# SUPER DRAFTY VERSION OF THIS SCRIPT!

# NOTE as of 2017-12-21:
#      This script assumes you already have OpenCAFE installed and configured!
#      Follow on work will make this "more" stand-alone, but we have to start somewhere.

# NOTE as of 2017-12-21:
#      This script assumes you are running it from the directory where it lives.

export PYTHONPATH=.:../../qe_coverage

echo "A good run, no ERRORs or FAILures should happen:"
cafe-parallel test test_decorators "$@"

echo "A bad run, errors should correspond to broken tests:"
cafe-parallel test bad_decorators "$@"
