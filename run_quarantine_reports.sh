#!/bin/sh

# Generate quarantined reports for every repo given as an argument.

search_hidden=""
if [ "$1" = "--search_hidden" ]; then
    search_hidden=" --search_hidden"
    shift
fi

# Create a temporary directory for the repos we want to run the reports on to be cloned into.
temp_dir=$(mktemp -d)

working_dir=$(pwd)
cd "$temp_dir"

# Clone the repos into a temp directory.
for repo_name in "$@"
do
    git clone "git@github.rackspace.com:"/"$repo_name".git --depth 1
done

cd "$working_dir"

# Process a report for every repo cloned
for repo_dir in "$temp_dir"/*
do
    ./run_quarantine_reports_on_repo.py "$repo_dir"$search_hidden
done

# Cleanup the temp directory
rm -rf "$temp_dir"
