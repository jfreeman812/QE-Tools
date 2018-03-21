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
RESULTS=`python -m unittest test_decorators "$@" 2>&1`
echo "$RESULTS"

FAILURES=`echo "$RESULTS" | grep "test_ok" | grep "skipped"`

if [[ ! -z  $FAILURES ]]; then
    echo "====================="
    echo "The following tests should have completed as 'ok', but were instead 'skipped':"
    echo "---------------------"
    echo $FAILURES
    echo "====================="
    exit 1
fi

echo "A bad run, an error should be printed, which corresponds to broken tests, but the tests should pass:"
python -m unittest bad_decorators "$@"
