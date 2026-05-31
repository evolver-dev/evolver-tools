#!/usr/bin/env python3
"""
json_to_table.py — Render JSON array as aligned ASCII table in terminal.

Reads JSON from stdin (default) or from a file argument. Handles:
  - Array of dicts: column headers = union of all dict keys, aligned left
  - Array of arrays: no headers, each sub-array is a row
  - Nested values are pretty-printed inline (json.dumps)

Usage:
  echo '[{"name":"Alice","age":30},{"name":"Bob","age":25}]' | python json_to_table.py
  python json_to_table.py data.json
  python json_to_table.py --header-labels "ID,Name,Role" data.json
"""

import argparse
import json
import sys


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Render JSON array as aligned ASCII table in terminal"
    )
    parser.add_argument(
        "file",
        nargs="?",
        default=None,
        help="JSON file path (omit to read from stdin)",
    )
    parser.add_argument(
        "--header-labels",
        default=None,
        help="Comma-separated column labels for array-of-arrays input. "
        "Ignored for dict input (uses dict keys).",
    )
    parser.add_argument(
        "--max-width",
        type=int,
        default=None,
        help="Truncate cell content to N characters (appends '...')",
    )
    return parser.parse_args(argv)


def load_json(filepath):
    """Load JSON from file or stdin."""
    if filepath:
        with open(filepath, "r") as f:
            return json.load(f)
    else:
        data = sys.stdin.read()
        if not data or not data.strip():
            print("Error: no input data (stdin is empty)", file=sys.stderr)
            sys.exit(1)
        return json.loads(data)


def flatten_value(v, max_width=None):
    """Convert a value to its string representation, pretty-printing dicts/lists."""
    if v is None:
        s = ""
    elif isinstance(v, (dict, list)):
        s = json.dumps(v, ensure_ascii=False, default=str)
    else:
        s = str(v)
    if max_width is not None and len(s) > max_width:
        s = s[: max_width - 3] + "..."
    return s


def collect_headers(rows):
    """Union of all keys across all dicts, preserving insertion order."""
    seen = {}
    for row in rows:
        if isinstance(row, dict):
            for k in row:
                seen.setdefault(k, None)
    return list(seen.keys())


def fmt_row(cells, widths):
    """Return a single formatted row line given cell values and column widths."""
    parts = []
    for i, w in enumerate(widths):
        val = cells[i] if i < len(cells) else ""
        parts.append(f" {val.ljust(w)} ")
    return "|" + "|".join(parts) + "|"


def fmt_separator(widths):
    """Return a separator line (dashes between columns)."""
    parts = []
    for w in widths:
        parts.append("-" * (w + 2))
    return "|" + "|".join(parts) + "|"


def render_table(rows, headers=None, max_width=None):
    """Render rows as an aligned ASCII table. Prints directly."""
    if not rows:
        print("(empty array)")
        return

    is_dicts = isinstance(rows[0], dict)

    if is_dicts:
        headers = headers or collect_headers(rows)
        # Build cell matrix: each row is a list of string values
        matrix = []
        for row in rows:
            r = []
            for h in headers:
                v = row.get(h) if isinstance(row, dict) else None
                r.append(flatten_value(v, max_width))
            matrix.append(r)
    else:
        # Array of arrays — no headers unless provided
        matrix = []
        for row in rows:
            r = [flatten_value(cell, max_width) for cell in row]
            matrix.append(r)

    # Compute column widths
    if headers:
        widths = [len(h) for h in headers]
    else:
        widths = []
        if matrix:
            ncols = max(len(r) for r in matrix)
            widths = [0] * ncols

    for row in matrix:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(cell))

    # Render
    if headers:
        print(fmt_row(headers, widths))
        print(fmt_separator(widths))
    for row in matrix:
        print(fmt_row(row, widths))


def main(argv=None):
    args = parse_args(argv)
    try:
        data = load_json(args.file)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON — {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: file not found — {args.file}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data, list):
        print("Error: top-level JSON must be an array (got %s)" % type(data).__name__, file=sys.stderr)
        sys.exit(1)

    if not data:
        print("(empty array)")
        return

    # Parse optional header labels
    labels = None
    if args.header_labels:
        labels = [s.strip() for s in args.header_labels.split(",")]

    render_table(data, headers=labels, max_width=args.max_width)


# === Auto-registration metadata ===
TOOL_META = {
    "name": "json-to-table",
    "func": "main",
    "desc": "Render JSON array as aligned ASCII table in terminal",
}

if __name__ == "__main__":
    main()
