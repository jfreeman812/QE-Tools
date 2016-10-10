#! /bin/sh

if [ "$1" = "--setup" ] ; then
    shift
    if ! ./env-setup.sh ; then
        echo environment setup failed, aborting self-checks
        exit 1
    fi
fi

# From this point on any command that fails should cause an exit.
set -e

echo running flake8...
flake8 .

