#!/usr/bin/env python3
"""csv-view — CSV/TSV viewer that prints formatted tables with auto-delimiter detection."""

import csv
import io
import os
import sys

TOOL_META = {
    "name": "csv-view",
    "func": "main",
    "desc": "View CSV/TSV files as formatted tables. Usage: csv-view file.csv [--head N] [--tail N]",
}


def detect_delimiter(first_line):
    """Auto-detect delimiter: tab, comma, semicolon, pipe."""
    candidates = {"\t": 0, ",": 0, ";": 0, "|": 0}
    for ch in candidates:
        candidates[ch] = first_line.count(ch)
    # Prefer tab if it appears, otherwise best comma/separator
    if candidates["\t"] > 0:
        return "\t"
    # Find delimiter with highest count
    best_delim = ","
    best_count = 0
    for d, count in candidates.items():
        if count > best_count:
            best_count = count
            best_delim = d
    if best_count == 0:
        return ","  # fallback
    return best_delim


def read_table(filepath, head=None, tail=None):
    """Read and parse CSV/TSV file, return (rows, delimiter, has_header)."""
    if not os.path.isfile(filepath):
        print(f"Error: file not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)

    if not content.strip():
        print("(empty file)")
        sys.exit(0)

    # Detect delimiter from first line
    first_line = content.split("\n", 1)[0]
    delimiter = detect_delimiter(first_line)

    reader = csv.reader(io.StringIO(content), delimiter=delimiter)
    all_rows = [row for row in reader]

    if not all_rows:
        print("(no data)")
        sys.exit(0)

    if head is not None and tail is not None:
        rows = all_rows[:head] + all_rows[-tail:]
    elif head is not None:
        rows = all_rows[:head]
    elif tail is not None:
        rows = all_rows[-tail:]
    else:
        rows = all_rows

    return rows, delimiter


def format_table(rows):
    """Return a formatted string with aligned columns."""
    if not rows:
        return "(no data)"

    # Calculate column widths
    num_cols = max(len(row) for row in rows) if rows else 0
    if num_cols == 0:
        return "(no columns)"

    col_widths = [0] * num_cols
    for row in rows:
        for i, cell in enumerate(row):
            if i < num_cols:
                col_widths[i] = max(col_widths[i], len(cell))

    # Cap width at 120 to prevent extreme wrapping
    col_widths = [min(w, 120) for w in col_widths]

    # Build separator line
    sep = "─" * (sum(col_widths) + len(col_widths) * 3 + 1)

    lines = [sep]
    for row_idx, row in enumerate(rows):
        parts = []
        for i in range(num_cols):
            val = row[i] if i < len(row) else ""
            if len(val) > 120:
                val = val[:117] + "..."
            parts.append(val.ljust(col_widths[i]))
        lines.append("│ " + " │ ".join(parts) + " │")
        if row_idx == 0:
            lines.append(sep)  # after header

    lines.append(sep)
    return "\n".join(lines)


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: csv-view <file> [--head N] [--tail N]")
        print()
        print("Options:")
        print("  --head N     Show only first N rows")
        print("  --tail N     Show only last N rows")
        print("  --head N --tail N   Show first N and last N rows")
        print()
        print("Auto-detects delimiter (comma, tab, semicolon, pipe).")
        return

    filepath = args[0]
    head = None
    tail = None

    i = 1
    while i < len(args):
        if args[i] == "--head" and i + 1 < len(args):
            try:
                head = int(args[i + 1])
            except ValueError:
                print("Error: --head requires an integer", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--tail" and i + 1 < len(args):
            try:
                tail = int(args[i + 1])
            except ValueError:
                print("Error: --tail requires an integer", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            i += 1

    rows, delimiter = read_table(filepath, head, tail)
    print(f"File: {filepath}  (delimiter: {repr(delimiter)})")
    print()
    print(format_table(rows))


if __name__ == "__main__":
    main()
