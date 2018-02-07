#! /bin/bash

CURRENT_BASEDIR="$(basename $( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd ))"
./$CURRENT_BASEDIR/build-docs.sh $@
ghp-import -p docs/
