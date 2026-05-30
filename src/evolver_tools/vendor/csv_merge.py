#!/usr/bin/env python3
"""csv-merge — Merge multiple CSV files by column or row."""
import sys, os, csv, json
from pathlib import Path
from collections import OrderedDict

TOOL_META = {
    "name": "csv-merge",
    "desc": "Merge multiple CSV files (by column or row)",
    "func": "main",
}

def merge_rows(files, sep=","):
    """Merge CSV files by appending rows (vertically)."""
    headers_seen = []
    all_rows = []
    for f in files:
        with open(f, newline="") as fh:
            reader = csv.reader(fh, delimiter=sep)
            try:
                header = next(reader)
            except StopIteration:
                continue
            if not headers_seen:
                headers_seen = header
            for row in reader:
                all_rows.append(row)
    return headers_seen, all_rows

def merge_columns(files, sep=",", key_col=0):
    """Merge CSV files by key column (like a join)."""
    merged = OrderedDict()
    headers = []
    first = True
    for f in files:
        with open(f, newline="") as fh:
            reader = csv.reader(fh, delimiter=sep)
            try:
                header = next(reader)
            except StopIteration:
                continue
            if first:
                headers = header
                first = False
            else:
                # Merge additional columns from this file
                for row in reader:
                    key = row[key_col] if len(row) > key_col else ""
                    if key not in merged:
                        merged[key] = [key] + [""] * (len(header) - 1)
                    # This is simplified - a proper merge would match columns by name
        # Re-read for data
        with open(f, newline="") as fh:
            reader = csv.reader(fh, delimiter=sep)
            for row in reader:
                if row:
                    merged[row[0]] = row
    return headers, list(merged.values())

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Merge multiple CSV files")
    parser.add_argument("input", nargs="+", help="CSV files to merge")
    parser.add_argument("-o", "--output", default="", help="Output file")
    parser.add_argument("-m", "--mode", choices=["rows", "cols"], default="rows", help="Merge mode")
    parser.add_argument("-s", "--sep", default=",", help="Separator")
    parser.add_argument("--key", type=int, default=0, help="Key column for column merge")
    args = parser.parse_args()

    if args.mode == "rows":
        headers, rows = merge_rows(args.input, sep=args.sep)
    else:
        headers, rows = merge_columns(args.input, sep=args.sep, key_col=args.key)

    output = args.output or "-"
    if output == "-":
        writer = csv.writer(sys.stdout, delimiter=args.sep)
        writer.writerow(headers)
        writer.writerows(rows)
    else:
        with open(output, "w", newline="") as f:
            writer = csv.writer(f, delimiter=args.sep)
            writer.writerow(headers)
            writer.writerows(rows)
        print(f"Merged {len(args.input)} files → {output} ({len(rows)} rows)")

if __name__ == "__main__":
    main()
