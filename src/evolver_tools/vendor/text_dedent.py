#!/usr/bin/env python3
"""text-dedent — Remove common leading whitespace from text.

Usage: text-dedent
       echo "    hello" | text-dedent
       text-dedent file.txt
       text-dedent --leading 4 file.txt  # remove exactly 4 spaces
"""

import sys
import textwrap


def _auto_dedent(lines):
    if not lines:
        return []
    non_empty = [l for l in lines if l.strip()]
    if not non_empty:
        return lines
    prefix = min((len(l) - len(l.lstrip())) for l in non_empty)
    return [l[prefix:] if len(l) >= prefix else l for l in lines]


def main():
    args = sys.argv[1:]
    if '-h' in args or '--help' in args:
        print(__doc__)
        return

    leading = None
    filepath = None
    for i, a in enumerate(args):
        if a == '--leading' and i + 1 < len(args):
            leading = int(args[i + 1])
        elif not a.startswith('-'):
            filepath = a

    try:
        if filepath:
            with open(filepath) as f:
                raw = f.read()
        else:
            raw = sys.stdin.read()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    lines = raw.splitlines(keepends=True)
    if leading is not None:
        result = ''.join(l[leading:] if len(l) > leading else l for l in lines)
    else:
        stripped = textwrap.dedent(raw)
        result = stripped

    print(result, end='')


TOOL_META = {
    "name": "text-dedent",
    "func": "main",
    "desc": "Remove common leading whitespace from text"
}
