#!/bin/sh

function usage {
    echo
    echo "$0: <name-of-coverage-script-to-run> <name-of-repo-to-clone> [optional-parameters-to-coverage-script]"
    echo
    echo "    the name of the repo to clone should be in the form Organization/repo-name"
    echo "    do not include the URL or the trailing '.git'"
    exit 1
}

coverage_tool="$1"
if ! shift ; then
    echo
    echo "ERROR: Missing required coverage tool parameter"
    usage
fi

repo_name="$1"
if ! shift ; then
    echo
    echo "ERROR: Missing required repo name to clone"
    usage
fi

# Create a temporary directory for the repo we want to run the reports on to be cloned into.
temp_dir=$(mktemp -d)

(cd "$temp_dir" ; git clone "git@github.rackspace.com:/${repo_name}.git" --depth 1)

# Process the reports for the repo.
for repo_dir in "$temp_dir"/*
do
    $coverage_tool "$repo_dir" "$@"
done

# Cleanup the temp directory
rm -rf "$temp_dir"
