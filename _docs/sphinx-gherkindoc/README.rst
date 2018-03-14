sphinx-gherkindoc
=================

``sphinx-gherkindoc`` is a tool designed to take a directory, recursively find all the feature files and markup files, and convert them into files that can then be included in Sphinx-based documentation. This script was inspired by ``sphinx-apidoc``.

For the most basic usage, an input (``<gherkin_path>``) and output (``<output_path>``) path must be provided. The output path files can then be incorporated into any larger documentation created, either by hand or through ``sphinx-apidoc``.

Optionally, a list of ``fnmatch``-compatible patterns can be added to the argument list that indicate files and/or folders that should be excluded from processing.

The script also accepts a number of optional arguments. The script fully documents each optional parameter and most mirror their counterpart in ``sphinx-apidoc``. One notable addition is the step glossary(``-G``, ``--step-glossary``). This directive allows a glossary of all the step definitions and which files use that definition, including the line number.
