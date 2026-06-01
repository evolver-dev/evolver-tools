#!/usr/bin/env python3
"""csv2json — Convert CSV files to JSON."""
import csv
import json
import sys

TOOL_META = {
    "name": "csv2json",
    "func": "main",
    "desc": "Convert CSV to JSON. Usage: csv2json [file.csv] [--pretty] [--output file.json]",
}

def main():
    args = sys.argv[1:]
    pretty = False
    input_file = None
    output_file = None
    i = 0
    while i < len(args):
        if args[i] == "--pretty":
            pretty = True
        elif args[i] == "--output" and i + 1 < len(args):
            output_file = args[i + 1]
            i += 1
        elif not args[i].startswith("-"):
            input_file = args[i]
        i += 1
    try:
        if input_file:
            with open(input_file, "r") as f:
                reader = csv.DictReader(f)
                data = list(reader)
        else:
            reader = csv.DictReader(sys.stdin)
            data = list(reader)
    except Exception as e:
        print(f"Error reading CSV: {e}", file=sys.stderr)
        sys.exit(1)
    if not data:
        print("[]")
        return
    indent = 2 if pretty else None
    output = json.dumps(data, indent=indent, ensure_ascii=False, default=str)
    if output_file:
        with open(output_file, "w") as f:
            f.write(output)
        print(f"Written: {output_file} ({len(data)} rows)")
    else:
        print(output)

if __name__ == "__main__":
    main()
