#!/bin/sh

# Generate quarantined reports for the given repo name, and interface type.  If desired provide
# optional product directory specifier with -p <product_dir_name>

# Create a temporary directory for the repo we want to run the reports on to be cloned into.
temp_dir=$(mktemp -d)

working_dir=$(pwd)
cd "$temp_dir"

# Clone the repo into a temp directory.
git clone "git@github.rackspace.com:"/"$1".git --depth 1

# Remove the 1st argument for the repo name, as it is no longer needed.
shift

cd "$working_dir"

# Process the reports for the repo.
for repo_dir in "$temp_dir"/*
do
    ./run_test_reports_on_repo.py "$repo_dir" "$@"
done

# Cleanup the temp directory
rm -rf "$temp_dir"
