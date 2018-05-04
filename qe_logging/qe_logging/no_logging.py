'''
Import this module to suppress logging output. No functions need to be called.

The use case here is that you want to build utility scripts from components
that contain logging statements, and want to avoid the annoying messages
from the logging module that say there are no handlers defined, and/or you
want to avoid logging messages coming out unexpectedly based on the default
values for the logging modules root handler, import this module.
'''

import logging
logging.getLogger().addHandler(logging.NullHandler())
