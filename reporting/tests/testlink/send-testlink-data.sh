#! /bin/bash

# Getting data from TestLink involves doing an export from their UI
# or making an API call that we don't yet have implemented.
# Either way, there would be identity/credential info to manage.
# Instead, we're taking a toy example of already exported TestLink XML
# and making sure that the coverage tool is able to upload it to Splunk.

coverage-testlink --leading-categories-to-strip 1 testlink_self_test_data.xml "QE Tools Self Test" gui
