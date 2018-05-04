#!/usr/bin/env python

# This is a helper program for testing the no_logging capability.

import logging
import os

logger = logging.getLogger('arbitrary.name.here')

if 'NO_LOG' in os.environ:
    from qe_logging import no_logging

# In python 2 this will provoke a no handlers found message and
# the actual message will be suppressed.
# In python 3 this message will be printed.
# So in both cases, output will be generated,
# even though it is different output.
logger.critical('provoke output with this call')
