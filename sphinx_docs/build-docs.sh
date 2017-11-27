#! /bin/bash

export GIT_COMMIT_ID=$(git rev-parse HEAD)
export GIT_ORIGIN_URL=$(git config --get remote.origin.url)
if [ -z "${SPHINX_CONF_PATH}" ]; then
    SPHINX_CONF_PATH="."
fi
if [ ! -f "${SPHINX_CONF_PATH}/conf.py" ]; then
    echo "cannot locate the Sphinx conf.py file; exiting."; exit 1
fi

# Quick and easy, for us, and for Jenkins:
if [ "$1" = "--setup" ] ; then
    shift
    if ! ./env-setup.sh ; then
        echo environment setup failed, aborting self-checks
        exit 1
    fi
fi

# cp -rf sphinx_docs/ _docs/
sphinx-build -c $SPHINX_CONF_PATH -E . docs/
