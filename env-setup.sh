#! /bin/sh

if [ -z "${VIRTUAL_ENV+x}" ] ; then
    echo "Error: Not running in virtual environment, setup aborted."
    exit 1
fi
echo Setting up "$VIRTUAL_ENV"
echo
pip install -U flake8
echo
echo
echo