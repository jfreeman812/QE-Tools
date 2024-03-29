#! /bin/sh

source ./check-venv.sh

if [ -z "${VIRTUAL_ENV+x}" ] ; then
    echo "Error: Not running in virtual environment, setup aborted."
    exit 1
fi
echo Setting up "$VIRTUAL_ENV"
echo
pip install -U -r requirements.txt
pip install -U -r development.txt
for extra in "${@:1}"; do
    pip install -e .[$extra]
done
. ./path-setup.sh
echo
echo
echo
