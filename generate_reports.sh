#!/bin/sh

# Deliberate choice that this step should not fail because of reporting errors.
# We want to generate as many reports as possible, so any issues with one report
# should not keep us from generating others.

# using hours-minutes-seconds makes for hard to read file names,
# so we use the build number to distinguish between different runs on the same day.


prefix=$(date +%Y-%m-%d)-"${BUILD_NUMBER}"

easy_repos="aric-qe-ui afroast"
repos="${easy_repos} rba_roast"

for repo in QE-Tools $repos
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

for repo in $easy_repos
do
    (cd "$repo" ; stats.py -r > "../${prefix}-${repo}.csv" 2>&1)
done

(cd "rba_roast/af" ; stats.py -r > "../../${prefix}-rba_af_api.csv" 2>&1)
(cd "rba_roast/aric" ; stats.py -r > "../../${prefix}-rba_aric_api.csv" 2>&1)

echo

ls -l *.csv

echo
