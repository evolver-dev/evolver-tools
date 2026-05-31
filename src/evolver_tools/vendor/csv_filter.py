#!/usr/bin/env python3
"""csv_filter.py — Filter CSV rows by column value matching.

Usage:
    cat data.csv | python csv_filter.py --column name --value Alice
    python csv_filter.py data.csv --column age --value 30
    python csv_filter.py data.csv --column city --value "New York" --delimiter ';'
    python csv_filter.py data.csv --column status --value active --invert
"""

from __future__ import annotations

import csv
import sys
import argparse
from typing import Dict, List, Sequence, TextIO


TOOL_META = {
    "name": "csv-filter",
    "func": "main",
    "desc": "Filter CSV rows by column value",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Filter CSV rows by column value matching.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        default=None,
        help="CSV file path (omit or use '-' to read from stdin)",
    )
    parser.add_argument(
        "--column",
        required=True,
        help="Column name to filter on",
    )
    parser.add_argument(
        "--value",
        required=True,
        help="Value to match (exact string match)",
    )
    parser.add_argument(
        "--delimiter",
        default=",",
        help="CSV delimiter character (default: ',')",
    )
    parser.add_argument(
        "--invert",
        action="store_true",
        default=False,
        help="Invert match — print rows where column does NOT equal value",
    )
    return parser


def open_input(file_arg: str | None) -> TextIO:
    """Return a file handle for the given argument or stdin."""
    if file_arg is None or file_arg == "-":
        return sys.stdin
    return open(file_arg, newline="")


def filter_rows(
    reader: csv.DictReader,
    column: str,
    value: str,
    invert: bool,
) -> List[Dict[str, str]]:
    """Filter rows from a DictReader where column matches (or doesn't match) value."""
    results: List[Dict[str, str]] = []
    for row in reader:
        cell = row.get(column, "")
        if invert:
            if cell != value:
                results.append(row)
        else:
            if cell == value:
                results.append(row)
    return results


def write_rows(rows: List[Dict[str, str]], fieldnames: Sequence[str], delimiter: str) -> None:
    """Write filtered rows to stdout as CSV."""
    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames, delimiter=delimiter)
    writer.writeheader()
    writer.writerows(rows)


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    fh = open_input(args.file)
    try:
        reader = csv.DictReader(fh, delimiter=args.delimiter)
        if not reader.fieldnames:
            sys.exit("error: CSV has no header row (column names required)")

        fieldnames = reader.fieldnames

        if args.column not in fieldnames:
            sys.exit(
                f"error: column '{args.column}' not found in CSV header. "
                f"Available columns: {', '.join(fieldnames)}"
            )

        rows = filter_rows(reader, args.column, args.value, args.invert)
    finally:
        if fh is not sys.stdin:
            fh.close()

    write_rows(rows, fieldnames, args.delimiter)


if __name__ == "__main__":
    main()
