"""
net-analyzer — entry point.

Handles the --tui flag and dispatches CLI commands.
"""

import sys
import argparse

from . import cli
from . import tui


def main() -> None:
    """Main entry point for net-analyzer."""
    # Quick check for --tui before argparse does heavy lifting
    if "--tui" in sys.argv[1:]:
        tui.main()
        return

    # Quick help/version
    if not sys.argv[1:]:
        cli.print_help()
        return

    if sys.argv[1] in ("-h", "--help"):
        cli.print_help()
        return

    if sys.argv[1] in ("-v", "--version"):
        print(f"net-analyzer v{__import__('net_analyzer').__version__}")
        return

    # Dispatch to CLI commands
    cli.dispatch(sys.argv[1:])


if __name__ == "__main__":
    main()
