# QE Test Coverage Reports For Gherkin Feature Files

## Overview
`stats.py` parses a directory hierarchy, starting with the current working directory, and
builds a report based on the containing Gherkin feature files (any files ending with
`.feature`).

## Implementation Details
The script starts traversing the directories starting with the current working directory
at time of execution. `stats.py` converts the directory hierarchy into Categories for the
report, up to 3 folders deep. If the final folder is called `features`, this folder name
is **not** used as a category.

## Usage
Without any parameters, `stats.py` will perform tag validation, ensuring the tags conform
with the tagging requiremnt [DEFINE SOMEWHERE]. If any errors are found, the command
returns with a non-zero status as well as printing each error on stdout.

`stats.py` is strict about only permitting the tags defined in the `tags.md` file. For
parsing legacy Gherkin, the flag `--legacy` can be provided, which will silence errors for
unknown tags. As the name implies, this should only be used for reporting on legacy
systems.

Using the `-r` (or `--report`) flag generates the coverage report in CSV format. The
optional `--json` flag can be provided to produce the coverage report in JSON. these
reports will be output onto stdout.

By default, `stats.py` utilizes the `tags.md` file found in the same directory. If an
alternate tags file is needed, it may be provided via `t FILE_PATH` (or `--tagsfile
FILE_PATH`)

The error reports, by default, are a single line with the error message and line number on
which the error was found. The `-e` flag allow for additional error formats:
 * csv - A CSV file containing the error message, file name, line number, and path
 * grep - A colon-separated string of the full path, line number, and error message.

NOTE: In the presence of errors, the main report body itself will have placeholders, but
the submission of a report when there are errors is very **strongly** discouraged.
