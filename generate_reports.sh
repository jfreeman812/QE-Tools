#!/bin/sh

# Deliberate choice that this step should not fail because of reporting errors.
# We want to generate as many reports as possible, so any issues with one report
# should not keep us from generating others.

# using hours-minutes-seconds makes for hard to read file names,
# so we use the build number to distinguish between different runs on the same day.


prefix="$(date +%Y-%m-%d)-${BUILD_NUMBER:-XX}"

repos="QE-Tools aric-qe-ui afroast rba_roast"

for repo in $repos
do
    echo Updating $repo 
    if [ ! -d "$repo" ]; then
        git clone git@github.rackspace.com:AutomationServices/"$repo".git
    fi
    (cd "$repo" ; git reset --hard ; git pull origin master )
    echo
    echo
done

PATH=$(pwd)/QE-Tools:"$PATH"
echo PATH = $PATH
echo


# cleanup from the last run(s).
# We can't do this at the end because the post-build step
# needs these files to archive.
rm -f *.csv


# Now scan all the directories where tagging reports are wanted.
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
