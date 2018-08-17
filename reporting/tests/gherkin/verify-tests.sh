set -e
(cd good; coverage-gherkin api "Unit::Tests" --dry-run)
(cd bad; coverage-gherkin api "Unit::Tests" --dry-run 2>&1 | sed -e 's/^[^:]*://') > actual_output.txt
diff expected_output.txt actual_output.txt
rm actual_output.txt
