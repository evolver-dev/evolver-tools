#!/usr/bin/env python3
"""merge-json — Deep merge multiple JSON files.

Usage:
    merge-json base.json patch.json [patch2.json ...]
    cat base.json | merge-json - patch.json

Merges arrays by concatenation, dicts by recursive update.
Numbers/types are overwritten by the last source.
"""

import json
import sys
import os

TOOL_META = {
    "name": "merge-json",
    "func": "main",
    "desc": "Deep merge multiple JSON files (arrays concatenate, dicts recurse)",
}


def merge(a, b):
    """Deep merge b into a (mutates a)."""
    if isinstance(a, dict) and isinstance(b, dict):
        for k in b:
            if k in a:
                a[k] = merge(a[k], b[k])
            else:
                a[k] = b[k]
        return a
    if isinstance(a, list) and isinstance(b, list):
        a.extend(b)
        return a
    return b


def load_json(source):
    """Load JSON from a file path or stdin marker '-'.
    Returns (data, label) where label is used in error messages."""
    if source == "-":
        return json.load(sys.stdin), "<stdin>"
    with open(source) as f:
        return json.load(f), source


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print("Usage: merge-json base.json patch.json [patch2.json ...]")
        print("       cat base.json | merge-json - patch.json")
        print("Deep merge multiple JSON files. Arrays concatenate, dicts recurse.")
        return

    # Load base
    try:
        base, label = load_json(args[0])
    except FileNotFoundError:
        print(f"Error: file not found — {args[0]}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON in {args[0]}: {e}", file=sys.stderr)
        sys.exit(1)

    # Apply patches
    for path in args[1:]:
        try:
            patch, plabel = load_json(path)
        except FileNotFoundError:
            print(f"Error: file not found — {path}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: invalid JSON in {path}: {e}", file=sys.stderr)
            sys.exit(1)
        try:
            base = merge(base, patch)
        except TypeError as e:
            print(f"Error: type conflict merging {plabel} into base: {e}", file=sys.stderr)
            sys.exit(1)

    json.dump(base, sys.stdout, indent=2, sort_keys=False)
    print()


if __name__ == "__main__":
    main()
