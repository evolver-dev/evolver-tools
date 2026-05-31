#!/usr/bin/env python3
"""csv-concat — Concatenate multiple CSV files, preserving headers."""
TOOL_META = {"name": "csv-concat", "func": "main", "desc": "Concatenate CSV files vertically (union mode)"}

import csv
import sys
import os


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print("Usage: csv-concat <file.csv> [file.csv...]")
        print("Concatenate CSV files with same headers.")
        print("  csv-concat a.csv b.csv c.csv > combined.csv")
        print("  csv-concat --skip-header a.csv b.csv  (keep first header only)")
        return

    skip_header = False
    if args[0] == "--skip-header":
        skip_header = True
        args = args[1:]

    if not args:
        print("No files specified", file=sys.stderr)
        sys.exit(1)

    for path in args:
        if not os.path.exists(path):
            print(f"Error: {path} not found", file=sys.stderr)
            sys.exit(1)

    writer = csv.writer(sys.stdout, lineterminator="\n")
    header_written = False

    for i, path in enumerate(args):
        with open(path, "r", newline="") as f:
            reader = csv.reader(f)
            try:
                header = next(reader)
            except StopIteration:
                continue  # empty file

            if not header_written:
                writer.writerow(header)
                header_written = True
            elif i > 0 and skip_header:
                # Already wrote header from first file
                pass

            for row in reader:
                writer.writerow(row)


if __name__ == "__main__":
    main()
