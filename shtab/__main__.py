from __future__ import absolute_import
import sys

from .main import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]) or 0)
