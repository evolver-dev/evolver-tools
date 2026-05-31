#!/usr/bin/env python3
"""csv-head — Display first N rows of a CSV file.

Usage: csv-head data.csv
       csv-head data.csv -n 20
       csv-head data.csv --columns name,email
       csv-head data.csv --format table
       cat data.csv | csv-head -n 5

Options:
  -n, --lines N         Number of rows to show (default: 10)
  -c, --columns NAMES   Comma-separated column names to show
  -f, --format FMT      Output format: csv (default) or table
  --no-header           Input has no header row
  -h, --help            Show this help message
"""

import csv
import io
import os
import sys

TOOL_META = {
    "name": "csv-head",
    "func": "main",
    "desc": "Display first N rows of a CSV file",
}


def read_input(filepath=None):
    """Read CSV data from file or stdin. Returns (content, source_name)."""
    if filepath:
        if not os.path.isfile(filepath):
            print(f"Error: file not found: {filepath}", file=sys.stderr)
            sys.exit(1)
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)
        return content, filepath
    else:
        try:
            content = sys.stdin.read()
        except KeyboardInterrupt:
            sys.exit(1)
        if not content.strip():
            print("(no input)", file=sys.stderr)
            sys.exit(1)
        return content, "<stdin>"


def parse_csv(content):
    """Parse CSV content into list of rows using csv.reader."""
    reader = csv.reader(io.StringIO(content))
    return [row for row in reader]


def filter_columns(rows, column_names, has_header):
    """Filter rows to only include specified columns.

    column_names is a list of column names (if has_header) or column indices.
    """
    if not rows or not column_names:
        return rows

    if has_header:
        header = rows[0]
        indices = []
        for name in column_names:
            name = name.strip()
            found = False
            for i, h in enumerate(header):
                if h.strip() == name:
                    indices.append(i)
                    found = True
                    break
            if not found:
                print(f"Error: column '{name}' not found in header", file=sys.stderr)
                sys.exit(1)
    else:
        # No header — column_names are 1-based indices
        indices = []
        for name in column_names:
            name = name.strip()
            try:
                idx = int(name) - 1
                if idx < 0:
                    print(f"Error: column index must be >= 1, got {name}", file=sys.stderr)
                    sys.exit(1)
                indices.append(idx)
            except ValueError:
                print(f"Error: without --no-header, column names must be integers, got '{name}'", file=sys.stderr)
                sys.exit(1)

    filtered = []
    for row in rows:
        new_row = [row[i] if i < len(row) else "" for i in indices]
        filtered.append(new_row)

    return filtered


def format_csv(rows):
    """Output rows as CSV."""
    writer = csv.writer(sys.stdout)
    for row in rows:
        writer.writerow(row)


def format_table(rows):
    """Output rows as an aligned table."""
    if not rows:
        return

    num_cols = max(len(row) for row in rows) if rows else 0
    if num_cols == 0:
        return

    col_widths = [0] * num_cols
    for row in rows:
        for i, cell in enumerate(row):
            if i < num_cols:
                col_widths[i] = max(col_widths[i], len(cell))

    for row in rows:
        parts = []
        for i in range(num_cols):
            val = row[i] if i < len(row) else ""
            parts.append(val.ljust(col_widths[i]))
        print("  ".join(parts))


def print_usage():
    """Print usage information."""
    print(__doc__.strip())


def main():
    args = sys.argv[1:]

    filepath = None
    lines = 10
    column_names = None
    output_format = "csv"
    has_header = True

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("-h", "--help"):
            print_usage()
            return
        elif arg in ("-n", "--lines") and i + 1 < len(args):
            try:
                lines = int(args[i + 1])
                if lines < 0:
                    print("Error: --lines/-n requires a non-negative integer", file=sys.stderr)
                    sys.exit(1)
            except ValueError:
                print("Error: --lines/-n requires an integer", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif arg in ("-c", "--columns") and i + 1 < len(args):
            column_names = [c.strip() for c in args[i + 1].split(",")]
            i += 2
        elif arg in ("-f", "--format") and i + 1 < len(args):
            fmt = args[i + 1].lower()
            if fmt not in ("csv", "table"):
                print(f"Error: --format/-f must be 'csv' or 'table', got '{fmt}'", file=sys.stderr)
                sys.exit(1)
            output_format = fmt
            i += 2
        elif arg == "--no-header":
            has_header = False
            i += 1
        elif arg.startswith("-"):
            print(f"Error: unknown option '{arg}'. Use --help for usage.", file=sys.stderr)
            sys.exit(1)
        else:
            if filepath is not None:
                print(f"Error: unexpected argument '{arg}'. Only one file path allowed.", file=sys.stderr)
                sys.exit(1)
            filepath = arg
            i += 1

    # Read input
    content, source_name = read_input(filepath)

    if not content.strip():
        print("(empty file)")
        sys.exit(0)

    # Parse CSV
    rows = parse_csv(content)

    if not rows:
        print("(no data)")
        sys.exit(0)

    total_rows = len(rows)

    # Determine data rows based on header
    if has_header and total_rows > 0:
        header = rows[0]
        data_rows = rows[1:]
    else:
        header = None
        data_rows = rows

    # Slice first N data rows
    if lines > 0 and lines < len(data_rows):
        data_rows = data_rows[:lines]

    # Reconstruct rows with optional header
    if header is not None:
        display_rows = [header] + data_rows
    else:
        display_rows = data_rows

    # Filter columns if requested
    if column_names:
        display_rows = filter_columns(display_rows, column_names, has_header)

    # Output
    if output_format == "csv":
        format_csv(display_rows)
    else:
        format_table(display_rows)


if __name__ == "__main__":
    main()
