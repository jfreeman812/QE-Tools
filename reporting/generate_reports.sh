#!/bin/sh

# Generate test coverage reports based on Gherkin tags.
#

# Report file name will contain date/time stamp.
# using hours-minutes-seconds makes for hard to read file names,
# so we use the build number to distinguish between different runs on the same day.

prefix="$(date +%Y-%m-%d)-${BUILD_NUMBER:-XX}"

github_root="git@github.rackspace.com:"

# --in-place is to allow this to be used to generate reports in place on existing
# repos so we can individually track our own status, or test out the report generator, etc.

checkout_repos=true
if [ "$1" = "--in-place" ]; then
    checkout_repos=false
    shift
fi

cleanup_old_csvs=true
if [ "$1" = "--dirty" ]; then
    cleanup_old_csvs=false
    shift
fi

if $checkout_repos ; then
    for repo_spec in AutomationServices/QE-Tools "$@"
    do
        repo="${repo_spec#*/}"
        echo Updating "$repo"
        if [ ! -d "$repo" ]; then
            git clone "$github_root"/"$repo_spec".git
            # Make sure we don't ever accidently push these repos.
            (cd "$repo" && git remote set-url --push origin DISABLE)
        fi
        # reset --hard is here because of lessons learned in other Jenkins
        # repos where sometimes files would be changed and cause the pull
        # to need to merge and then the merge would fail.
        (cd "$repo" ; git reset --hard ; git pull origin master )
        echo
        echo
    done

    PATH=$(pwd)/QE-Tools:"$PATH"
    echo PATH = $PATH
    echo
fi


if $cleanup_old_csvs ; then
    # cleanup from the last run(s).
    # We can't do this at the end of this run, because the Jenkins post-build step
    # needs these files to still be around so it can archive them.
    rm -f *.csv
fi


# Scan all the directories where tagging reports are wanted.
# the file tag_report_name.txt is used to indicate where in the tree
# a report should be rooted, and the first line of the file is used
# to provide a unique part of the report's file name.
# If any run finds an error, print a message, but keep going so we can
# generate as many reports as possible.
# Exit with an error status if any run had an error.

found_error=0

for dir in $(find . -iname tag_report_name.txt | sed 's#/[^/]*$##')
do
     unique_part=$(sed -n -e 1p ${dir}/tag_report_name.txt)
     csv_name="${prefix}-${unique_part}.csv"
     echo Scanning ${dir} into ${csv_name}
     if ! (cd "$dir" ; stats.py -r )> "${csv_name}" 2>&1 ; then
        echo "    Error in stats for ${dir}"
        found_error=1
     fi
done

echo


ls -l *.csv

echo

exit $found_error