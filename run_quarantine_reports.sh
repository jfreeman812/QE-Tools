#!/bin/sh

# Generate quarantined reports for every repo given as an argument.
github_root="git@github.rackspace.com:"

# Create a temporary directory for the repos we want to run the reports on to be cloned into.
temp_dir=`tempfile`
rm -f "$temp_dir"
mkdir "$temp_dir"

# Clone the repos into a temp directory.
for repo_name in "$@"
do
    git -C "$temp_dir" clone "$github_root"/"$repo_name".git --depth 1
done

# Process a report for every repo cloned
for repo_dir in "$temp_dir"/*
do
    ./run_quarantine_reports_on_repo.py "$repo_dir"
done

# Cleanup the temp directory
rm -rf "$temp_dir"
