# QE-Tools
To hold tools and configurations used by the AF and ARIC QE Teams


* tags.md - describes the tagging we use for controlling our Gherkin tests and for generating test coverage reports.
* stats.py - reads the tags.md and uses that to analyze Gherkin feature files and generate a test coverage report.
* checkboxestiming.py - a quick and dirty script that read the JSON of an executed CheckBoxes process and look-for/report-on slow APIs.
* test_tags.py - still experimental code.
* tox.ini - initial stab at tox based testing.
* cafe - directory that might represent an OpenCAFE version of these tools - still WIP.
