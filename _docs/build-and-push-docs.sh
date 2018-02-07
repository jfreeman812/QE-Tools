#! /bin/bash

./_docs/build-docs.sh $@
ghp-import -p docs/
