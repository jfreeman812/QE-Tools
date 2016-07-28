# Test scoping / coverage reporting.

To support our requirement to generate test coverage reporting,
we have some data, tools, and conventions.

### Data:
* tags.md 
  * describes the groups / categories for reporting
  * defines values within those groups, both as tags for Gherkin and string equivalents for reporting.

### Tools:
* stats.py - generates a coverage report for Gherkin feature test files.
  * reads tags.md to know what tags to expect/enforce/report on.
  * reads a directory tree of feature files to check tags for and generate report for.

### Conventions (not enforced by the tools):
* The filesystem heirarchy of feature files is reflected in columns of the generated report.
  * For ARIC, we have a defined list of directories to represent the high level features.
* As Feature summary lines and Scenario summary lines are copied directly into the report.
  * For ARIC API testing, we use the rest operation (POST/GET/etc) as a prefix to the Scenario Summary line.
  * For ARIC API testing, we include the API endpoint in parenthesis at the end of the Feature Summary line.
