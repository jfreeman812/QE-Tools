#! /bin/sh

do_setup=false

if [ "$1" = "--setup" ] ; then
    shift
    do_setup=true
fi

if $do_setup ; then
    ./env-setup.sh
fi

# From this point on any command that fails should cause an exit.
set -e

echo running flake8...
flake8 .

