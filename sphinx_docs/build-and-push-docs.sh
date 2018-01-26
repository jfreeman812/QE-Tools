#! /bin/bash

./sphinx_docs/build-docs.sh $@
ghp-import -p docs/
