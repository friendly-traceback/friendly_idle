__version__ = "0.2.1"

import sys

py = sys.version_info

if py < (3, 8, 10) or (py > (3, 9) < (3, 9, 5)):
    print("Python 3.8.10 or greater than 3.9.4 is required.")
    sys.exit()
