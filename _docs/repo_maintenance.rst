Repository Maintenance
======================

A collection of notes and procedures
to record the collective team knowledge,
and prevent the need for
"how did we do this last time?" questions and discussions.

Adding a new Python version to test
-----------------------------------

To subject our ``tox`` tests to an additional Python version,
the following are required:


    * update ``path-setups.sh`` to install and make available the new version:
        * add a line for ``pyenv install -s {version}`` so that it is installed if not present
        * add that version number to the ``pyenv local {version} {numbers} {available}`` line
    * add the version nickname to ``tox.ini`` (e.g. ``3.7.0`` would need ``py37`` added to the ``envlist`` key)
    * update ``_docs/contributing.rst`` to note the additional version
