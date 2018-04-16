#! /bin/bash

# Preliminary script to ensure that the data injection feature works properly
#
# This script assumes you are running it from the directory where it lives.

if ! source ./generate-expected-injected-coverage.sh ; then
    echo
    echo Error when generating expected injected coverage, aborting
    exit 2
fi

# Check that the injected coverage report contents haven't changed:
# NOTE: $JSON_FILE and $COVERAGE_DIR come from the generate-expected-injected-coverage.sh script.
if diff --ignore-all-space expected-injected-coverage.json "$JSON_FILE" ; then
    echo
    echo The csv data injection worked properly! Removing generated coverage files.
    rm -rf $COVERAGE_DIR
fi
