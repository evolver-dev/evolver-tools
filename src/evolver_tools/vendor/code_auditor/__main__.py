"""
Entry point for `python -m code_auditor`.
"""

import sys
from .cli import main

if __name__ == "__main__":
    sys.exit(main())
