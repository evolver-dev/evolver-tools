#!/usr/bin/env python3
"""json-sort — Sort JSON keys alphabetically.

Usage: json-sort input.json
       cat data.json | json-sort
       json-sort input.json --sorted output.json
"""

import sys
import json


def _sort(obj):
    if isinstance(obj, dict):
        return {k: _sort(v) for k, v in sorted(obj.items())}
    elif isinstance(obj, list):
        return [_sort(item) for item in obj]
    return obj


def main():
    args = sys.argv[1:]
    if '-h' in args or '--help' in args:
        print(__doc__)
        return

    filepath = None
    output_path = None
    indent = 2
    for i, a in enumerate(args):
        if a == '--indent' and i + 1 < len(args):
            indent = int(args[i + 1])
        elif a.startswith('-'):
            continue
        elif filepath is None:
            filepath = a
        elif output_path is None:
            output_path = a

    try:
        if filepath:
            with open(filepath) as f:
                data = json.load(f)
        else:
            data = json.load(sys.stdin)
        sorted_data = _sort(data)
        result = json.dumps(sorted_data, indent=indent, ensure_ascii=False)
        if output_path:
            with open(output_path, 'w') as f:
                f.write(result)
            print(f"Written to {output_path}")
        else:
            print(result)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


TOOL_META = {
    "name": "json-sort",
    "func": "main",
    "desc": "Sort JSON keys alphabetically, recursively"
}
