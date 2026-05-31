#!/usr/bin/env python3
"""diff-csv — Diff two CSV files by key column. Shows added/removed/changed rows."""
import sys
import os
import argparse
import csv
import io


def detect_delimiter(path):
    """Detect CSV delimiter by sampling first line."""
    try:
        with open(path, "r") as f:
            first_line = f.readline().strip()
    except IOError as e:
        print(f"Error reading {path}: {e}", file=sys.stderr)
        sys.exit(1)
    # Count delimiters
    for delim in [",", ";", "\t", "|"]:
        count = first_line.count(delim)
        if count >= 1:
            return delim
    return ","


def read_csv(path, key_column, ignore_case, delimiter=None):
    """Read CSV file into dict keyed by the key column."""
    if delimiter is None:
        delimiter = detect_delimiter(path)
    rows = {}
    headers = []
    try:
        with open(path, "r", newline="") as f:
            reader = csv.reader(f, delimiter=delimiter)
            headers = next(reader, [])
            for row_num, row in enumerate(reader, 2):
                if not row or all(c.strip() == "" for c in row):
                    continue
                # Pad short rows
                while len(row) < len(headers):
                    row.append("")
                key = row[key_column] if key_column < len(row) else ""
                if ignore_case:
                    key = key.lower()
                rows[key] = row
    except csv.Error as e:
        print(f"CSV error in {path}: {e}", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"Error reading {path}: {e}", file=sys.stderr)
        sys.exit(1)
    return headers, rows


def format_row(headers, row, color_prefix="", color_suffix=""):
    """Format a row for display."""
    parts = []
    for i, h in enumerate(headers):
        val = row[i] if i < len(row) else ""
        parts.append(f"{h}={val}")
    return f"{color_prefix}{' | '.join(parts)}{color_suffix}"


def green(text):
    return f"\033[32m{text}\033[0m"


def red(text):
    return f"\033[31m{text}\033[0m"


def yellow(text):
    return f"\033[33m{text}\033[0m"


def cyan(text):
    return f"\033[36m{text}\033[0m"


def main():
    parser = argparse.ArgumentParser(
        description="Diff two CSV files by key column."
    )
    parser.add_argument("file1", help="First CSV file")
    parser.add_argument("file2", help="Second CSV file")
    parser.add_argument("-k", "--key", default="id", help="Key column name or index (default: id)")
    parser.add_argument("--ignore-case", action="store_true", help="Case-insensitive key matching")
    parser.add_argument("-d", "--delimiter", default=None, help="CSV delimiter (auto-detect if not set)")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    parser.add_argument("--summary-only", action="store_true", help="Show summary only, no detailed diff")

    args = parser.parse_args()

    if not os.path.isfile(args.file1):
        print(f"Error: File not found: {args.file1}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(args.file2):
        print(f"Error: File not found: {args.file2}", file=sys.stderr)
        sys.exit(1)

    delimiter = args.delimiter
    if delimiter:
        delimiter = delimiter.replace("\\t", "\t")

    # Read both files
    headers1, rows1 = read_csv(args.file1, 0, args.ignore_case, delimiter)
    headers2, rows2 = read_csv(args.file2, 0, args.ignore_case, delimiter)

    # Determine key column index
    key_idx = 0
    try:
        key_idx = int(args.key)
    except ValueError:
        key_name = args.key
        if key_name in headers1:
            key_idx = headers1.index(key_name)
        elif key_name in headers2:
            key_idx = headers2.index(key_name)
        else:
            print(f"Error: Key column '{key_name}' not found in either file", file=sys.stderr)
            sys.exit(1)

    # Use headers from file2 (or file1 if file2 empty)
    headers = headers2 if headers2 else headers1

    # Reread with correct key index if needed
    if key_idx != 0:
        headers1, rows1 = read_csv(args.file1, key_idx, args.ignore_case, delimiter)
        headers2, rows2 = read_csv(args.file2, key_idx, args.ignore_case, delimiter)
        headers = headers2 if headers2 else headers1

    keys1 = set(rows1.keys())
    keys2 = set(rows2.keys())

    added = keys2 - keys1
    removed = keys1 - keys2
    common = keys1 & keys2

    changed = set()
    for k in common:
        r1 = rows1[k]
        r2 = rows2[k]
        if r1 != r2:
            changed.add(k)

    if args.no_color:
        g = lambda t: t
        r = lambda t: t
        y = lambda t: t
        c = lambda t: t
    else:
        g = green
        r = red
        y = yellow
        c = cyan

    total_added = len(added)
    total_removed = len(removed)
    total_changed = len(changed)
    total_unchanged = len(common) - total_changed

    if not args.summary_only:
        if added:
            print(c(f"=== Added rows ({total_added}) ==="))
            for k in sorted(added):
                print(g(f"+  {rows2[k]}"))

        if removed:
            print(c(f"\n=== Removed rows ({total_removed}) ==="))
            for k in sorted(removed):
                print(r(f"-  {rows1[k]}"))

        if changed:
            print(c(f"\n=== Changed rows ({total_changed}) ==="))
            for k in sorted(changed):
                r1 = rows1[k]
                r2 = rows2[k]
                print(y(f"~  Key: {k}"))
                for i, h in enumerate(headers):
                    v1 = r1[i] if i < len(r1) else ""
                    v2 = r2[i] if i < len(r2) else ""
                    if v1 != v2:
                        print(f"    {h}: {r(v1)} -> {g(v2)}")

    # Summary
    print(c(f"\n--- Summary ---"))
    print(f"  Added:     {g(str(total_added))}")
    print(f"  Removed:   {r(str(total_removed))}")
    print(f"  Changed:   {y(str(total_changed))}")
    print(f"  Unchanged: {total_unchanged}")
    print(f"  File1 rows: {len(rows1)}, File2 rows: {len(rows2)}")



# === Auto-registration metadata ===
TOOL_META = {
    "name": "diff-csv",
    "func": "main",
    "desc": 'Row-level diff of CSV files by key column',
}

if __name__ == "__main__":
    main()
