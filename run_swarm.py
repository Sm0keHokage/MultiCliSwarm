#!/usr/bin/env python3
import sys
import os

# Append 'src' to system path to enable running without installation
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from multicliswarm.cli import main

if __name__ == "__main__":
    main()
