#!/usr/bin/env python3
"""Entry point for db-mate. Routes to CLI or TUI mode."""

import sys
from .cli import entry, print_help
from .tui import run_tui


def main():
    args = sys.argv[1:]

    # Extract --db <path> early for TUI too
    db_path = None
    clean_args = []
    i = 0
    while i < len(args):
        if args[i] == "--db" and i + 1 < len(args):
            db_path = args[i + 1]
            i += 2
        else:
            clean_args.append(args[i])
            i += 1
    args = clean_args

    if "--tui" in args:
        args.remove("--tui")
        run_tui(db_path)
        return

    if not args or args[0] in ("--help", "-h"):
        print_help()
        return

    entry(args, db_path)


if __name__ == "__main__":
    main()
