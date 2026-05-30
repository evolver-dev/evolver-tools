"""
log_hawk.__main__ — Entry point for ``python -m log_hawk`` and ``log-hawk`` CLI.

Dispatches to the CLI parser (which itself can launch the TUI).
"""

import sys

from .cli import entry_point


def main():
    entry_point()


if __name__ == "__main__":
    main()
