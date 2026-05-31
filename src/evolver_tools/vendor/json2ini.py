#!/usr/bin/env python3
"""json2ini — Convert JSON to INI format."""
import json
import os
import sys

TOOL_META = {
    "name": "json2ini",
    "func": "main",
    "desc": "Convert JSON to INI format. Usage: json2ini <file.json>",
}

def to_ini(data):
    lines = []
    if not isinstance(data, dict):
        print("Error: JSON must be an object", file=sys.stderr)
        sys.exit(1)
    for section, values in data.items():
        lines.append(f"[{section}]")
        if isinstance(values, dict):
            for key, val in values.items():
                lines.append(f"{key} = {val}")
        else:
            lines.append(f"value = {values}")
        lines.append("")
    return "\n".join(lines)

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: json2ini <file.json>")
        print("       cat file.json | json2ini")
        return
    filepath = None
    for a in args:
        if not a.startswith("-"):
            filepath = a
            break
    try:
        if filepath:
            with open(filepath) as f:
                data = json.load(f)
        else:
            data = json.loads(sys.stdin.read())
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    print(to_ini(data))

if __name__ == "__main__":
    main()
