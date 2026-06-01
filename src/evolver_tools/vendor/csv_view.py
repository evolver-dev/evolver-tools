#!/usr/bin/env python3
"""csv-view — CSV file viewer with formatted table output.

Features:
  - Accept CSV file as argument or via stdin pipe
  - Auto-detect delimiter (comma, tab, semicolon, pipe)
  - --head / -n: show first N rows (default: 10)
  - --tail / -t: show last N rows
  - --columns / -c: list column names only
  - --sort column_name: sort by column
  - --filter "column=value": filter rows
  - --json: JSON output
  - Pretty table format with aligned columns, headers, and separators
  - Handles quoted fields and escaped commas
  - Shows row count and column count
  - Pure stdlib (csv, sys, os, json)
"""

import csv
import io
import json
import os
import sys

TOOL_META = {
    "name": "csv-view",
    "func": "main",
    "desc": "CSV file viewer with table formatting. Auto-detects delimiter, filters, sorts, JSON output.",
}


def detect_delimiter(first_line):
    """Auto-detect delimiter from first line of CSV data."""
    candidates = {"\t": 0, ",": 0, ";": 0, "|": 0}
    in_quote = False
    for ch in first_line:
        if ch == '"':
            in_quote = not in_quote
        elif not in_quote and ch in candidates:
            candidates[ch] += 1

    # If tab appears, prefer it (TSV)
    if candidates["\t"] > 0:
        return "\t"

    best_delim = ","
    best_count = 0
    for d, count in candidates.items():
        if count > best_count:
            best_count = count
            best_delim = d

    return best_delim if best_count > 0 else ","


def parse_csv_data(content, delimiter):
    """Parse CSV content string into list of rows."""
    reader = csv.reader(io.StringIO(content), delimiter=delimiter)
    return [row for row in reader]


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
        # Read from stdin
        try:
            content = sys.stdin.read()
        except KeyboardInterrupt:
            sys.exit(1)
        if not content.strip():
            print("(no input)", file=sys.stderr)
            sys.exit(1)
        return content, "<stdin>"


def format_table(rows, delimiter, sort_col=None, filter_expr=None):
    """Parse, filter, sort, and format CSV rows as a pretty table."""
    if not rows:
        return "(no data)", 0, 0

    num_cols = max(len(row) for row in rows) if rows else 0
    if num_cols == 0:
        return "(no columns)", 0, 0

    # First row is header
    header = rows[0]
    data_rows = rows[1:]

    # --filter
    if filter_expr:
        if "=" not in filter_expr:
            print(f"Error: invalid filter format '{filter_expr}'. Use column=value.", file=sys.stderr)
            sys.exit(1)
        col_name, filter_val = filter_expr.split("=", 1)
        filter_val = filter_val.strip().strip('"').strip("'")
        col_name = col_name.strip()

        # Find column index
        col_idx = None
        for i, h in enumerate(header):
            if h.strip() == col_name:
                col_idx = i
                break
        if col_idx is None:
            print(f"Error: column '{col_name}' not found in header: {header}", file=sys.stderr)
            sys.exit(1)

        filtered = []
        for row in data_rows:
            if col_idx < len(row) and row[col_idx].strip().strip('"').strip("'") == filter_val:
                filtered.append(row)
        data_rows = filtered

    # --sort
    if sort_col:
        sort_col = sort_col.strip()
        col_idx = None
        for i, h in enumerate(header):
            if h.strip() == sort_col:
                col_idx = i
                break
        if col_idx is None:
            print(f"Error: column '{sort_col}' not found in header: {header}", file=sys.stderr)
            sys.exit(1)

        def sort_key(row):
            val = row[col_idx] if col_idx < len(row) else ""
            # Try numeric sort
            try:
                return (0, float(val))
            except (ValueError, TypeError):
                return (1, val.lower())

        data_rows.sort(key=sort_key)

    # Build display rows (header + data)
    display_rows = [header] + data_rows
    row_count = len(data_rows)
    col_count = len(header)

    # Calculate column widths
    col_widths = [0] * num_cols
    for row in display_rows:
        for i, cell in enumerate(row):
            if i < num_cols:
                # Account for display width (strip ANSI, use visible length)
                col_widths[i] = max(col_widths[i], len(cell))

    # Cap width to prevent extreme wrapping
    col_widths = [min(w, 120) for w in col_widths]

    # Build table
    total_width = sum(col_widths) + len(col_widths) * 3 + 1
    sep = "─" * total_width

    lines = [sep]
    for row_idx, row in enumerate(display_rows):
        parts = []
        for i in range(num_cols):
            val = row[i] if i < len(row) else ""
            if len(val) > 120:
                val = val[:117] + "..."
            parts.append(val.ljust(col_widths[i]))
        lines.append("│ " + " │ ".join(parts) + " │")
        if row_idx == 0:
            lines.append(sep)  # separator after header

    lines.append(sep)
    return "\n".join(lines), row_count, col_count


def output_json(rows, delimiter, sort_col=None, filter_expr=None):
    """Output rows as JSON array of objects (using header as keys)."""
    if not rows or len(rows) < 1:
        print("[]")
        return

    header = rows[0]
    data_rows = rows[1:]

    # --filter
    if filter_expr:
        if "=" not in filter_expr:
            print(f"Error: invalid filter format '{filter_expr}'. Use column=value.", file=sys.stderr)
            sys.exit(1)
        col_name, filter_val = filter_expr.split("=", 1)
        filter_val = filter_val.strip().strip('"').strip("'")
        col_name = col_name.strip()
        col_idx = None
        for i, h in enumerate(header):
            if h.strip() == col_name:
                col_idx = i
                break
        if col_idx is None:
            print(f"Error: column '{col_name}' not found", file=sys.stderr)
            sys.exit(1)
        filtered = []
        for row in data_rows:
            if col_idx < len(row) and row[col_idx].strip().strip('"').strip("'") == filter_val:
                filtered.append(row)
        data_rows = filtered

    # --sort
    if sort_col:
        sort_col = sort_col.strip()
        col_idx = None
        for i, h in enumerate(header):
            if h.strip() == sort_col:
                col_idx = i
                break
        if col_idx is None:
            print(f"Error: column '{sort_col}' not found", file=sys.stderr)
            sys.exit(1)

        def sort_key(row):
            val = row[col_idx] if col_idx < len(row) else ""
            try:
                return (0, float(val))
            except (ValueError, TypeError):
                return (1, val.lower())

        data_rows.sort(key=sort_key)

    records = []
    for row in data_rows:
        record = {}
        for i, h in enumerate(header):
            record[h.strip()] = row[i] if i < len(row) else ""
        records.append(record)

    print(json.dumps(records, indent=2))


def print_columns(rows):
    """Print column names only."""
    if not rows:
        print("(no data)")
        return
    header = rows[0]
    print(f"Columns ({len(header)}):")
    for i, col in enumerate(header):
        print(f"  {i}: {col}")


def print_summary(row_count, col_count, source_name, delimiter, rows_total):
    """Print summary line."""
    readable_delim = {
        "\t": "tab",
        ",": "comma",
        ";": "semicolon",
        "|": "pipe",
    }.get(delimiter, repr(delimiter))
    print(f"File: {source_name}  |  {row_count} rows x {col_count} columns  |  delimiter: {readable_delim}  |  total rows in file: {rows_total}")


def main():
    args = sys.argv[1:]

    # Parse arguments
    filepath = None
    head_count = 10
    tail_count = None
    show_columns = False
    sort_col = None
    filter_expr = None
    json_output = False

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("-h", "--help"):
            print("Usage: csv-view [file] [options]")
            print()
            print("Arguments:")
            print("  file                  CSV file to view (omit to read from stdin)")
            print()
            print("Options:")
            print("  -h, --help            Show this help message")
            print("  --head N, -n N        Show first N rows (default: 10)")
            print("  --tail N, -t N        Show last N rows")
            print("  --columns, -c         List column names only")
            print("  --sort column_name    Sort rows by column")
            print('  --filter "col=val"    Filter rows where column equals value')
            print("  --json                Output as JSON")
            print()
            print("Examples:")
            print("  csv-view data.csv")
            print("  csv-view data.csv --head 5")
            print("  csv-view data.csv --tail 20")
            print("  csv-view data.csv --columns")
            print("  csv-view data.csv --sort name")
            print('  csv-view data.csv --filter "status=active"')
            print("  csv-view data.csv --json")
            print("  cat data.csv | csv-view --head 5")
            return
        elif arg in ("--head", "-n") and i + 1 < len(args):
            try:
                head_count = int(args[i + 1])
            except ValueError:
                print("Error: --head/-n requires an integer", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif arg in ("--tail", "-t") and i + 1 < len(args):
            try:
                tail_count = int(args[i + 1])
            except ValueError:
                print("Error: --tail/-t requires an integer", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif arg in ("--columns", "-c"):
            show_columns = True
            i += 1
        elif arg == "--sort" and i + 1 < len(args):
            sort_col = args[i + 1]
            i += 2
        elif arg == "--filter" and i + 1 < len(args):
            filter_expr = args[i + 1]
            i += 2
        elif arg == "--json":
            json_output = True
            i += 1
        elif arg.startswith("-"):
            print(f"Error: unknown option '{arg}'. Use --help for usage.", file=sys.stderr)
            sys.exit(1)
        else:
            # Must be the file path
            filepath = arg
            i += 1

    # Read input
    content, source_name = read_input(filepath)

    if not content.strip():
        print("(empty file)")
        sys.exit(0)

    # Detect delimiter from first non-empty line
    first_line = ""
    for line in content.split("\n"):
        if line.strip():
            first_line = line
            break
    delimiter = detect_delimiter(first_line)

    # Parse all rows
    rows = parse_csv_data(content, delimiter)

    if not rows:
        print("(no data)")
        sys.exit(0)

    total_rows_in_file = len(rows) - 1  # minus header

    # --columns / -c
    if show_columns:
        print_columns(rows)
        return

    # Apply head/tail slicing
    if tail_count is not None:
        # Keep header, slice data rows
        header = rows[0]
        data_rows = rows[1:]
        if head_count is not None and head_count < len(data_rows):
            # Show first N and last N
            if tail_count > 0:
                sliced = data_rows[:head_count] + data_rows[-tail_count:]
            else:
                sliced = data_rows[:head_count]
        elif tail_count > 0:
            sliced = data_rows[-tail_count:]
        else:
            sliced = data_rows
        rows = [header] + sliced
    elif head_count is not None and head_count < (len(rows) - 1):
        rows = [rows[0]] + rows[1:1 + head_count]

    # --json
    if json_output:
        output_json(rows, delimiter, sort_col, filter_expr)
        return

    # Format and print table
    table, row_count, col_count = format_table(rows, delimiter, sort_col, filter_expr)
    print()
    print(table)
    print()
    print_summary(row_count, col_count, source_name, delimiter, total_rows_in_file)


if __name__ == "__main__":
    main()
