from pprint import pprint

import sys

from . import cah_config

for f in sys.argv[1:]:
    cah_config.load(f)
