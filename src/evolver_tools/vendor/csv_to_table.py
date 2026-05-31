#!/usr/bin/env python3
"""csv-to-table — Convert CSV input to an aligned ASCII table in the terminal.

Usage:
    csv-to-table data.csv
    csv-to-table --delimiter ';' data.csv
    cat data.csv | csv-to-table
    csv-to-table --delimiter $'\t' < data.tsv

Zero-dependency (stdlib only).
"""

import csv
import sys
import argparse


def _compute_widths(rows):
    """Return a list of max character widths per column across all rows."""
    if not rows:
        return []
    ncols = max(len(r) for r in rows) if rows else 0
    widths = [0] * ncols
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    return widths


def _fmt_row(cells, widths, sep="|"):
    """Format a single row as a line in the ASCII table."""
    parts = []
    for i, w in enumerate(widths):
        cell = cells[i] if i < len(cells) else ""
        parts.append(f" {cell:<{w}} ")
    return sep + sep.join(parts) + sep


def _fmt_separator(widths, left="+", mid="+", right="+", fill="-"):
    """Format a horizontal separator line."""
    segments = [fill * (w + 2) for w in widths]
    return left + mid.join(segments) + right


def _read_csv(stream, delimiter):
    """Read CSV data from an open stream and return a list of lists (strings)."""
    reader = csv.reader(stream, delimiter=delimiter)
    rows = []
    for row in reader:
        rows.append([str(cell) for cell in row])
    return rows


def main():
    parser = argparse.ArgumentParser(
        description="Convert CSV input to an aligned ASCII table."
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="CSV file path (omit to read from stdin)",
    )
    parser.add_argument(
        "--delimiter",
        default=",",
        help="CSV delimiter character (default: ',')",
    )
    parser.add_argument(
        "--no-header",
        action="store_true",
        help="Treat first row as data, not a header",
    )
    args = parser.parse_args()

    if args.file:
        try:
            with open(args.file, newline="") as f:
                rows = _read_csv(f, args.delimiter)
        except FileNotFoundError:
            print(f"Error: file not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)
    elif not sys.stdin.isatty():
        rows = _read_csv(sys.stdin, args.delimiter)
    else:
        parser.print_usage()
        print("error: no input (provide a file or pipe CSV data)", file=sys.stderr)
        sys.exit(1)

    if not rows:
        print("(empty)")
        return

    widths = _compute_widths(rows)
    sep_line = _fmt_separator(widths)

    print(sep_line)
    if not args.no_header and len(rows) >= 1:
        print(_fmt_row(rows[0], widths))
        print(_fmt_separator(widths, left="|", mid="|", right="|"))
        for row in rows[1:]:
            print(_fmt_row(row, widths))
        print(sep_line)
    else:
        for row in rows:
            print(_fmt_row(row, widths))
        print(sep_line)


# === Auto-registration metadata ===
TOOL_META = {
    "name": "csv-to-table",
    "func": "main",
    "desc": "Convert CSV to an aligned ASCII table in terminal",
}

if __name__ == "__main__":
    main()
