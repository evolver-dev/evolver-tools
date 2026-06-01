#!/usr/bin/env python3
"""
csv-sort — Sort CSV files by column.

Usage:
    csv-sort [--column COL] [--reverse] [--numeric] [FILE]

Arguments:
    FILE                  Input CSV file (reads from stdin if omitted)

Options:
    -c, --column COL      Column name or 1-based index to sort by (default: first column)
    -r, --reverse         Sort in descending order
    -n, --numeric         Sort values as numbers instead of text
    -h, --help            Show this help message and exit

Examples:
    csv-sort data.csv
    csv-sort -c 2 -r data.csv
    csv-sort -c "name" -n < data.csv
    cat data.csv | csv-sort -c "age" -n -r
"""

import csv
import sys


def main():
    args = sys.argv[1:]

    # Parse help
    if '-h' in args or '--help' in args:
        print((__doc__ or '').strip())
        return

    # Parse --column / -c
    column = None
    if '--column' in args:
        idx = args.index('--column')
        if idx + 1 < len(args):
            column = args[idx + 1]
            args = args[:idx] + args[idx + 2:]
    elif '-c' in args:
        idx = args.index('-c')
        if idx + 1 < len(args):
            column = args[idx + 1]
            args = args[:idx] + args[idx + 2:]

    # Parse flags
    reverse = '--reverse' in args or '-r' in args
    numeric = '--numeric' in args or '-n' in args
    args = [a for a in args if a not in ('--reverse', '-r', '--numeric', '-n')]

    # Remaining positional arg is file path (optional)
    filepath = args[0] if args else None

    try:
        if filepath:
            with open(filepath, newline='') as f:
                reader = csv.reader(f)
                rows = list(reader)
        else:
            reader = csv.reader(sys.stdin)
            rows = list(reader)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not rows:
        sys.exit(0)

    # Separate header from data
    header = rows[0]
    data = rows[1:]

    # Determine column index
    if column is None:
        col_idx = 0
    else:
        try:
            col_idx = int(column) - 1  # 1-based to 0-based
        except ValueError:
            # Column is a name — find it in the header
            try:
                col_idx = header.index(column)
            except ValueError:
                print(f"Error: column '{column}' not found in header: {header}", file=sys.stderr)
                sys.exit(1)

    if col_idx < 0:
        print(f"Error: column index must be 1 or greater", file=sys.stderr)
        sys.exit(1)

    # Sort
    try:
        if numeric:
            data.sort(key=lambda row: _safe_num(row[col_idx]), reverse=reverse)
        else:
            data.sort(key=lambda row: row[col_idx] if col_idx < len(row) else '', reverse=reverse)
    except IndexError:
        print(f"Error: column index {col_idx + 1} exceeds row width", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error during sort: {e}", file=sys.stderr)
        sys.exit(1)

    # Write output
    writer = csv.writer(sys.stdout)
    writer.writerow(header)
    writer.writerows(data)


def _safe_num(val):
    """Convert a string to float for numeric sorting, with fallback."""
    try:
        return float(val)
    except (ValueError, TypeError):
        return float('inf')


TOOL_META = {"name": "csv-sort", "func": "main", "desc": "Sort CSV files by column"}


if __name__ == '__main__':
    main()
