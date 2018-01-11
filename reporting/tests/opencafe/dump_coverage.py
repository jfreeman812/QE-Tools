# Debugging script for humans.
# Pretty print the contents of a coverage JSON file, which is just one JSON object per line.

import sys
import json

from pprint import pprint

map(pprint, map(json.loads, open(sys.argv[1]).readlines()))
