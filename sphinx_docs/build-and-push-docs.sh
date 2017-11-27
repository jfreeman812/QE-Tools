#! /bin/bash

./build-docs.sh $@
ghp-import -p docs/
