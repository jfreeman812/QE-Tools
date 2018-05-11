#! /bin/sh

source ./check-venv.sh

export PIP_INDEX_URL="https://artifacts.rackspace.net/artifactory/api/pypi/pypi/simple"

if [ "$1" = "--setup" ] ; then
    shift
    if ! ./env-setup.sh ; then
        echo environment setup failed, aborting self-checks
        exit 1
    fi
fi

# Capture all test output into a file
self_check_output='.self-test-stdout.log'
echo "output capture in $self_check_output"
echo
> $self_check_output

# From this point on any command that fails should cause an exit.
set -e

echo running flake8...
flake8 .
for f in */self-check.sh ; do
    echo running $f...
    (cd $(dirname $f); ./self-check.sh) >> $self_check_output
done

if [ "$BUILD_CAUSE" = "GHPRBCAUSE" ]; then
    echo "running Docs Link PR Commenter..."
    ./_docs/gh_doc_link.py $PR_COMMENT_TOKEN
    echo "checking if any sensitive files were changed..."
    sensitive_files="data_broker/__schema_version__.py"
    python sensitive_file_checker.py $PR_COMMENT_TOKEN $sensitive_files
    echo "checking to make sure package versions were updated if necessary..."
    python3 version_checker.py $PR_COMMENT_TOKEN
fi
