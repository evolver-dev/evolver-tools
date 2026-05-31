#!/usr/bin/env python3
"""text-wrap — Wrap text to specified column width.

Usage: text-wrap
       echo "long line here..." | text-wrap
       text-wrap file.txt
       text-wrap --width 60 file.txt
       text-wrap --indent "> " --width 50 file.txt
"""

import sys
import textwrap


def main():
    args = sys.argv[1:]
    if '-h' in args or '--help' in args:
        print(__doc__)
        return

    width = 80
    indent = None
    filepath = None

    i = 0
    while i < len(args):
        a = args[i]
        if a == '--width' and i + 1 < len(args):
            i += 1
            width = int(args[i])
        elif a == '--indent' and i + 1 < len(args):
            i += 1
            indent = args[i]
        elif not a.startswith('-'):
            filepath = a
        i += 1

    try:
        if filepath:
            with open(filepath) as f:
                text = f.read()
        else:
            text = sys.stdin.read()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    kwargs = {"width": width}
    if indent is not None:
        kwargs["initial_indent"] = indent
        kwargs["subsequent_indent"] = indent

    wrapped = textwrap.fill(text, **kwargs)
    print(wrapped)


TOOL_META = {
    "name": "text-wrap",
    "func": "main",
    "desc": "Wrap text to specified column width",
}
