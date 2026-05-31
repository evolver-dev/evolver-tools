#!/usr/bin/env python3
"""json-to-yaml — Convert JSON to YAML format.

Usage: json-to-yaml input.json
       cat input.json | json-to-yaml

Zero-dependency YAML-like output for simple JSON structures.
"""

import sys
import json


def _yaml_dump(obj, indent=0):
    prefix = "  " * indent
    if isinstance(obj, dict):
        if not obj:
            return "{}"
        lines = []
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                lines.append(f"{prefix}{k}:")
                lines.append(_yaml_dump(v, indent + 1))
            else:
                val = _yaml_val(v)
                lines.append(f"{prefix}{k}: {val}")
        return "\n".join(lines)
    elif isinstance(obj, list):
        if not obj:
            return "[]"
        lines = []
        for item in obj:
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}-")
                sub = _yaml_dump(item, indent + 1)
                lines.append(sub)
            else:
                lines.append(f"{prefix}- {_yaml_val(item)}")
        return "\n".join(lines)
    else:
        return f"{prefix}{_yaml_val(obj)}"

def _yaml_val(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    elif v is None:
        return "null"
    elif isinstance(v, str):
        if any(c in v for c in ":\"'"''":
            return f'"{v}"'
        return v
    return str(v)


def main():
    args = sys.argv[1:]
    if '-h' in args or '--help' in args:
        print(__doc__)
        return
    try:
        if args:
            with open(args[0]) as f:
                data = json.load(f)
        else:
            data = json.load(sys.stdin)
        print(_yaml_dump(data))
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON - {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


TOOL_META = {
    "name": "json-to-yaml",
    "func": "main",
    "desc": "Convert JSON to YAML format (stdlib, zero deps)"
}
