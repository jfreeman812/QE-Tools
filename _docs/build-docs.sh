#! /bin/bash

export GIT_COMMIT_ID=$(git rev-parse HEAD)
export GIT_ORIGIN_URL=$(git config --get remote.origin.url)
if [ -z "${SPHINX_CONF_PATH}" ]; then
    SPHINX_CONF_PATH="_docs"
fi
if [ ! -f "${SPHINX_CONF_PATH}/conf.py" ]; then
    echo "cannot locate the Sphinx conf.py file; exiting."; exit 1
fi

# Quick and easy, for us, and for Jenkins:
if [ "$1" = "--setup" ] ; then
    shift
    # While the requirements file is, by default, the same path as the conf.py file,
    # it is not guaranteed so needs to be explicitly referenced here
    if ! pip install -r _docs/requirements.txt ; then
        echo environment setup failed, aborting self-checks
        exit 1
    fi
fi

sphinx-build -c $SPHINX_CONF_PATH -aE . docs/
