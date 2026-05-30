#!/usr/bin/env python3
"""crypto-box entry point. Routes to CLI or TUI mode."""

import sys
from . import print_banner, __version__


def main():
    """Main entry: crypto-box [command] [options] or crypto-box tui."""
    if len(sys.argv) > 1 and sys.argv[1] == "tui":
        from crypto_box.tui import tui_main
        import curses
        curses.wrapper(tui_main)
        return

    from crypto_box.cli import cli_main
    cli_main()


if __name__ == "__main__":
    main()
