#!/usr/bin/env python3
"""json_merge — Merge multiple JSON files into one.

Usage: json_merge file1.json file2.json
       json_merge *.json --output merged.json
       json_merge base.json override.json --strategy deep

Merge strategies:
  - shallow (default): top-level keys only. Later files override earlier.
  - deep: recursive merge of nested dicts.
  - array: concatenate arrays.
"""

import json
import sys
import os
from copy import deepcopy

TOOL_META = {
    "name": "json_merge",
    "func": "main",
    "desc": "Merge multiple JSON files into one",
}


def deep_merge(a, b):
    """Recursively merge b into a."""
    result = deepcopy(a)
    for key in b:
        if key in result and isinstance(result[key], dict) and isinstance(b[key], dict):
            result[key] = deep_merge(result[key], b[key])
        else:
            result[key] = deepcopy(b[key])
    return result


def array_merge(a, b):
    """Merge arrays by concatenation."""
    if isinstance(a, dict) and isinstance(b, dict):
        result = deepcopy(a)
        for key in b:
            if key in result and isinstance(result[key], list) and isinstance(b[key], list):
                result[key] = result[key] + b[key]
            elif key in result and isinstance(result[key], dict) and isinstance(b[key], dict):
                result[key] = deep_merge(result[key], b[key])
            else:
                result[key] = deepcopy(b[key])
        return result
    elif isinstance(a, list) and isinstance(b, list):
        return a + b
    return b


def main():
    args = sys.argv[1:]
    files = []
    strategy = 'shallow'
    output = None

    i = 0
    while i < len(args):
        if args[i] in ('-h', '--help'):
            print(__doc__)
            return
        elif args[i] == '--strategy' and i + 1 < len(args):
            strategy = args[i + 1].lower()
            i += 2
        elif args[i] == '--output' and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        elif not args[i].startswith('--'):
            files.append(args[i])
            i += 1
        else:
            i += 1

    if len(files) < 2:
        print("Error: need at least 2 JSON files", file=sys.stderr)
        sys.exit(1)

    data = []
    for path in files:
        if not os.path.exists(path):
            print(f"Error: file not found: {path}", file=sys.stderr)
            sys.exit(1)
        with open(path) as f:
            data.append(json.load(f))

    result = data[0]
    for d in data[1:]:
        if strategy == 'deep':
            result = deep_merge(result, d)
        elif strategy == 'array':
            result = array_merge(result, d)
        else:
            # shallow
            result.update(d)

    if output:
        with open(output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Merged {len(files)} files -> {output}")
    else:
        print(json.dumps(result, indent=2))
