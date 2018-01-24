#! /bin/bash

# This script assumes you are running it from the directory where it lives.

# Preliminary script to make sure any changes
# to decorator code doesn't change the generated coverage data.

# Since the name of the coverage file is generated to be unique,
# make sure we have no coverage files already around.
shopt -s nullglob
if [ -n "$(echo coverage-*.json)" ]; then
    echo existing coverage files found, cannot proceed
    exit 2
fi

if ! ./generate-expected-coverage.sh ; then
    echo
    echo Error when generating expected coverage, aborting
    exit 2
fi

# Check that the coverage report contents haven't changed:
if diff expected-coverage-results.json coverage*.json  ; then
    echo
    echo No changes, removing temporary coverage file.
    rm -f coverage-*.json
fi
