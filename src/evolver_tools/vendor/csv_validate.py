#!/usr/bin/env python3
"""csv-validate — Validate CSV files for formatting issues."""
import csv
import os
import sys

TOOL_META = {
    "name": "csv-validate",
    "func": "main",
    "desc": "Validate CSV file format. Usage: csv-validate <file.csv>",
}

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: csv-validate <file.csv>")
        return
    filepath = args[0]
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    errors = []
    warnings = []
    with open(filepath, "r") as f:
        lines = f.readlines()
    if not lines:
        errors.append("File is empty")
    else:
        # Check header
        header = lines[0].strip()
        header_cols = next(csv.reader([header]))
        expected_cols = len(header_cols)
        if len(set(header_cols)) != len(header_cols):
            warnings.append(f"Header has duplicate column names: {header_cols}")
        # Check each row
        for i, line in enumerate(lines[1:], 2):
            line = line.strip()
            if not line:
                continue
            try:
                row = next(csv.reader([line]))
                if len(row) != expected_cols:
                    errors.append(f"Row {i}: expected {expected_cols} columns, got {len(row)}")
            except csv.Error as e:
                errors.append(f"Row {i}: CSV parse error — {e}")
            except StopIteration:
                errors.append(f"Row {i}: empty row after strip")
    if not errors and not warnings:
        print(f"✓ {filepath}: valid CSV ({len(lines) - 1} rows, {expected_cols} columns)")
    else:
        if errors:
            print(f"✗ ERRORS ({len(errors)}):")
            for e in errors:
                print(f"  {e}")
        if warnings:
            print(f"⚠ WARNINGS ({len(warnings)}):")
            for w in warnings:
                print(f"  {w}")
        if errors:
            sys.exit(1)

if __name__ == "__main__":
    main()
