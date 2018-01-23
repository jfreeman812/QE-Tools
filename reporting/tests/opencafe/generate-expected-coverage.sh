#! /bin/bash

# SUPER DRAFTY VERSION OF THIS SCRIPT!

# NOTE as of 2017-12-21:
#      This script assumes you already have OpenCAFE installed and configured!
#      Follow on work will make this "more" stand-alone, but we have to start somewhere.

# NOTE as of 2017-12-21:
#      This script assumes you are running it from the directory where it lives.

# Technically, the ../../qe_coverage part is not needed if that package
# has been installed, but it is here so that this script will run even
# in a bare virtual env.
export PYTHONPATH=.:../../qe_coverage
export COLLECT_TAGS_DATA_INTO=.

# Only run on the test_decorators module to avoid hitting the bad_decorators and any
# other iffy data...

RESULTS=$(cafe-parallel test test_decorators "$@" 2>&1)
echo "$RESULTS"

FAILURES=$(echo "$RESULTS" | fgrep "has been called")

if [[ ! -z  $FAILURES ]]; then
    echo "====================="
    echo "The following output should not have been seen:"
    echo "---------------------"
    echo $FAILURES
    echo "====================="
    exit 1
fi
