#! /bin/sh

if [ "$1" = "--setup" ] ; then
    shift
    ./env-setup.sh
fi

# From this point on any command that fails should cause an exit.
set -e

echo running flake8...
flake8 .

