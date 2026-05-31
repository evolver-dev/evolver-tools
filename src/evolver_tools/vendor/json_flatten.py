#!/usr/bin/env python3
"""json_flatten — Flatten nested JSON to dot-notation key=value pairs.

Usage: json_flatten data.json
       json_flatten data.json --sep /
       cat data.json | json_flatten

Useful for converting nested JSON to flat key-value format
for CSV export, env files, or debugging.
"""

import json
import sys
import os

TOOL_META = {
    "name": "json_flatten",
    "func": "main",
    "desc": "Flatten nested JSON to dot-notation key=value pairs",
}

def flatten(obj, parent_key='', sep='.'):
    items = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, (dict, list)):
                items.extend(flatten(v, new_key, sep=sep))
            else:
                items.append((new_key, v))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            new_key = f"{parent_key}{sep}{i}" if parent_key else str(i)
            if isinstance(v, (dict, list)):
                items.extend(flatten(v, new_key, sep=sep))
            else:
                items.append((new_key, v))
    else:
        items.append((parent_key, obj))
    return items


def main():
    args = sys.argv[1:]
    sep = '.'
    files = []

    i = 0
    while i < len(args):
        if args[i] == '--sep' and i + 1 < len(args):
            sep = args[i + 1]
            i += 2
        elif args[i] in ('-h', '--help'):
            print(__doc__)
            return
        else:
            files.append(args[i])
            i += 1

    if files:
        data = []
        for f in files:
            if not os.path.exists(f):
                print(f"Error: file not found: {f}", file=sys.stderr)
                sys.exit(1)
            with open(f) as fp:
                data.append(json.load(fp))
        if len(data) == 1:
            data = data[0]
    else:
        data = json.load(sys.stdin)

    items = flatten(data, sep=sep)
    for key, val in items:
        if val is None:
            val = 'null'
        elif isinstance(val, bool):
            val = str(val).lower()
        elif isinstance(val, (int, float)):
            val = str(val)
        print(f"{key}={val}")
