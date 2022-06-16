__version__ = "0.3.0"

import sys

py = sys.version_info

if py < (3, 8, 10) or (3, 9) < py < (3, 9, 5):
    print("Python version 3.8.10, or Python version greater than 3.9.4 is required.")
    sys.exit()
