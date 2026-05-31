#!/usr/bin/env python3
"""xml-format — Pretty-print / format XML files.

Usage: xml-format input.xml
       cat input.xml | xml-format
       xml-format input.xml output.xml
"""

import sys
import xml.dom.minidom


def main():
    args = sys.argv[1:]
    if '-h' in args or '--help' in args:
        print(__doc__)
        return
    try:
        if args:
            with open(args[0]) as f:
                raw = f.read()
        else:
            raw = sys.stdin.read()
        dom = xml.dom.minidom.parseString(raw)
        pretty = dom.toprettyxml(indent="  ")
        pretty = "\n".join(line for line in pretty.split("\n") if line.strip())
        if len(args) > 1:
            with open(args[1], 'w') as f:
                f.write(pretty)
        else:
            print(pretty)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


TOOL_META = {
    "name": "xml-format",
    "func": "main",
    "desc": "Pretty-print and format XML files (stdlib)"
}
