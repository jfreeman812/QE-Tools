#!/bin/bash

# This script is to collect and publish coverage metrics for an OpenCAFE test repo.


function missing {
    echo
    echo "ERROR: missing required $*"
    usage
}

function usage {
    echo
    echo "$0: [-h] [--no-clean] [--check-only] <default-interface-type> <product-name> <business-unit> <team> <open-cafe-command>..."
    echo
    echo "    if --no-clean is used, the temporary directory created will not be cleaned up"
    echo "       this is for humans who want to look at intermediate output"
    echo
    echo "    If --check-only is used, the metrics will be gathered, but not sent to splunk"
    echo
    echo "    default-interface-type is the default for when tests or directory names"
    echo "    don't specify which interface type they are for."
    echo
    echo "    product-name is the name of the product to use in the coverage reporting."
    echo "    (see QGTM-671, this should be temporary)"
    echo
    echo "    business-unit is the name of the business unit to use in the coverage reporting."
    echo
    echo "    team is the name of the team (sub-category of the business unit) to use in the coverage reporting."
    echo
    echo "    open-cafe-command... the rest of the parameters are the OpenCAFE command and parameters needed"
    echo "        to run your tests. They will be run with an environment variable set"
    echo "        to cause the coverage metrics to gathered and no test code will actually run."
    echo "        Do not use any tag filtering here as any tests filtered out will not have coverage reported."
    echo
    echo "Environment Variables used:"
    echo "JENKINS_URL - this is the name of the host under which the coverage metrics are reported."
    echo "            - if this is not defined, your local host name is used."
    echo 
    echo "SPLUNK_TOKEN - this is the secret needed to be able to publish coverage metrics to splunk."
    echo "             - if it is not defined and --check-only is not used, you will get an error."
    echo
    exit 1
}

publish=true
clean=true

if [ "$1" = "-h" ] ; then
    usage
fi

if [ "$1" = "--no-clean" ] ; then
    shift
    clean=false
fi

if [ "$1" = "--check-only" ] ; then
    shift
    publish=false
    echo "$0: Metrics will not be published."
else
    if [ "${SPLUNK_TOKEN-}" = "" ] ; then
        echo "Must supply SPLUNK_TOKEN env var or --check-only"
        usage
    fi
fi

default_interface_type="$1"
if ! shift ; then missing "default interface type" ; fi

product_name="$1"
if ! shift ; then missing "product name" ; fi

business_unit="$1"
if ! shift ; then missing "business unit" ; fi

team="$1"
if ! shift ; then missing "team" ; fi

if [ $# -le 0 ] ; then missing "open-cafe commands" ; fi

# Create a temporary directory for the metrics to be published in to.
temp_dir=$(mktemp -d)

export COLLECT_TAGS_DATA_INTO="$temp_dir"

# Run whatever open-cafe command has been given
"$@"

if $publish ; then
    echo About to publish metrics
    send_opencafe_tags_report \
        -o "$temp_dir" \
        --splunk_token "$SPLUNK_TOKEN" \
        "$temp_dir"/coverage*.json \
        "$product_name" \
        "$default_interface_type" \
        "$business_unit" \
        "$team"
fi

if $clean ; then
    # Cleanup the temp directory
    rm -rf "$temp_dir"
else
    echo
    echo "no cleanup done, temporary files are in:" "$temp_dir"
fi
