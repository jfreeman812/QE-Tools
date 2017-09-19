#!/bin/sh

# Generate quarantined reports for the given repo name, and interface type.  If desired provide
# optional product directory specifier with -p <product_dir_name>

search_hidden=""
if [ "$1" = "--search_hidden" ]; then
    search_hidden=" --search_hidden"
    shift
fi

repo_name="$1"
shift

# Create a temporary directory for the repo we want to run the reports on to be cloned into.
temp_dir=$(mktemp -d)

working_dir=$(pwd)
cd "$temp_dir"

# Clone the repo into a temp directory.
git clone "git@github.rackspace.com:"/"$repo_name".git --depth 1

cd "$working_dir"

# Process the reports for the repo.
for repo_dir in "$temp_dir"/*
do
    ./run_quarantine_reports_on_repo.py "$repo_dir" "$@""$search_hidden"
done

# Cleanup the temp directory
rm -rf "$temp_dir"
