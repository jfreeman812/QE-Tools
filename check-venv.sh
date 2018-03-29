#! /bin/bash
# source this file to make sure you are running in a Python virtual environment
# Use --check-proxy parameter if you want to propigate proxies for pip, etc..
if [ -z "${VIRTUAL_ENV+x}" ] ; then
    echo "Error: Not running in virtual environment, aborted."
    exit 1
fi
if [ "--check-proxy" == "$1" ]; then
    shift
    # Now check for proxy needed by Jenkins for pip installs.
    if [ "x$pip_http_proxy" != "x" ]; then
        export http_proxy="$pip_http_proxy"
        echo Setting http proxy: $http_proxy
    fi
    if [ "x$pip_https_proxy" != "x" ]; then
        export https_proxy="$pip_https_proxy"
        echo Setting https proxy: $https_proxy
    fi
fi
