QE Logging
==========

A collection of logging related helpers to provide, standard logging for QE.


- `setup_logging`_

setup_logging
-------------

This function will create all necessary logging directories, create two file handlers and apply
consistent formatting for QE logs.  One file handler will always write (or overwrite) to the same
file name in the top level of the ``log_directory``.  The second handlers will write to a new file
that is placed in a new time stamped directory on each test run.

Usage
~~~~~

The function requires a ``log_name_prefix`` that is prepended to the standard log name
({log_name_prefix}.master.log).  This log name will be the same for both handlers.

Additional ``*historical_log_dir_layers`` can be provided in order to partition the historical time
stamped directories into logical groupings.  A current use case for this is providing the test
environment as a ``*historical_log_dir_layers`` resulting in the time stamped directories being grouped
by test environment.

The default ``log_directory`` of 'logs' can be overridden if desired to have the logs placed in an
alternate location.

API Documentation
~~~~~~~~~~~~~~~~~

.. automodule:: qe_logging
    :members:
    :undoc-members:
    :show-inheritance:
