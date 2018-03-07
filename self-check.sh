#! /bin/sh

export PIP_INDEX_URL="https://artifacts.rackspace.net/artifactory/api/pypi/pypi/simple"

if [ "$1" = "--setup" ] ; then
    shift
    if ! ./env-setup.sh ; then
        echo environment setup failed, aborting self-checks
        exit 1
    fi
fi

# Capture all test output into a file
self_check_output='.self-test-stdout.log'
echo "output capture in $self_check_output"
echo
> $self_check_output

# From this point on any command that fails should cause an exit.
set -e

echo running flake8...
flake8 .
for f in */self-check.sh ; do
    echo running $f...
    (cd $(dirname $f); ./self-check.sh) >> $self_check_output
done
