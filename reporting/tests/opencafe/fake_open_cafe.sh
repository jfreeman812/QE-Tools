#! /bin/bash

# This is a script that can be used to fake open cafe coverage gathering
# to avoid having to have OpenCAFE installed.
# It basically fakes out the running of the coverage
# for testing the gathering and publishing script purposes.


function usage() {
    echo Usage: "$0 [error-results|no-results|duplicate-results]"
    echo
    echo "When invoked with:"
    echo "  no parameters:"
    echo "      copies the expected coverage results file to the directory given by the"
    echo "      COLLECT_TAGS_DATA_INTO environment variable."
    echo "  error-results:"
    echo "      exits with a non-zero error code and does not copy"
    echo "  no-results:"
    echo "      exits with success (0), but does not copy"
    echo "  duplicate-results:"
    echo "      copies the expected results file into two separate files and"
    echo "      exits with success (0)"
    echo
    exit 1
}

if [ "$1" = "-h" ] ; then
    usage
fi

if [ "${COLLECT_TAGS_DATA_INTO-}" = "" ] ; then
    echo Error: $0 - COLLECT_TAGS_DATA_INTO environment variable is not set
    exit 1
fi


if [ "$1" = "error-results" ] ; then
   echo $0 - Pretend this is your OpenCAFE run with errors
   exit 1
fi

if [ "$1" = "no-results" ] ; then
   exit 0
fi

cp expected-coverage-results.json $COLLECT_TAGS_DATA_INTO/coverageABC.json

if [ "$1" = "duplicate-results" ] ; then
    cp expected-coverage-results.json $COLLECT_TAGS_DATA_INTO/coverageDEF.json
fi

exit 0
