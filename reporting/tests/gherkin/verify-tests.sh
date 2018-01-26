set -e
(cd good; coverage-gherkin api --dry-run)
(cd bad; coverage-gherkin api --dry-run | sed -e 's/^[^:]*://') > actual_output.txt
diff expected_output.txt actual_output.txt
rm actual_output.txt
