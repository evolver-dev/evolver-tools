#!/usr/bin/env python3
"""csv-slice — Extract specific columns/rows from CSV files.

Usage: csv-slice input.csv --columns 1,3,5
       csv-slice input.csv --columns name,email --rows 1-10
       cat data.csv | csv-slice --columns 0-2
       csv-slice input.csv --rows 5,10-20 --columns name
"""

import sys
import csv

def main():
    args = sys.argv[1:]
    if '-h' in args or '--help' in args:
        print(__doc__)
        return

    col_spec = None
    row_spec = None
    filepath = None
    idx = 0
    while idx < len(args):
        if args[idx] in ('--columns', '-c'):
            idx += 1
            if idx < len(args):
                col_spec = args[idx]
        elif args[idx] in ('--rows', '-r'):
            idx += 1
            if idx < len(args):
                row_spec = args[idx]
        else:
            filepath = args[idx]
        idx += 1

    try:
        if filepath is None or filepath == '-':
            lines = sys.stdin.read().splitlines()
        else:
            with open(filepath, newline='') as f:
                lines = f.read().splitlines()
    except Exception as e:
        print(f"Error reading input: {e}", file=sys.stderr)
        sys.exit(1)

    if not lines:
        return

    reader = csv.reader(lines)
    rows = list(reader)
    if not rows:
        return

    # Parse column spec
    header = rows[0]
    if col_spec:
        cols = set()
        parts = col_spec.split(',')
        for p in parts:
            if '-' in p:
                a, b = p.split('-', 1)
                a = int(a) if a.isdigit() else (header.index(a) if a in header else -1)
                b = int(b) if b.isdigit() else (header.index(b) if b in header else -1)
                for c in range(a, b + 1):
                    if 0 <= c < len(header):
                        cols.add(c)
            else:
                c = int(p) if p.isdigit() else (header.index(p) if p in header else -1)
                if 0 <= c < len(header):
                    cols.add(c)
        col_indices = sorted(cols)
    else:
        col_indices = list(range(len(header)))

    # Parse row spec
    if row_spec:
        selected_rows = []
        parts = row_spec.split(',')
        header_first = True
        if header_first:
            selected_rows.append(0)
        for p in parts:
            if '-' in p:
                a, b = p.split('-', 1)
                for r in range(int(a), int(b) + 1):
                    if 1 <= r < len(rows):
                        selected_rows.append(r)
            else:
                r = int(p)
                if 1 <= r < len(rows):
                    selected_rows.append(r)
        selected_rows = sorted(set(selected_rows))
    else:
        selected_rows = list(range(len(rows)))

    # Output
    writer = csv.writer(sys.stdout)
    for r in selected_rows:
        writer.writerow([rows[r][c] if c < len(rows[r]) else '' for c in col_indices])


TOOL_META = {
    "name": "csv-slice",
    "func": "main",
    "desc": "Extract columns/rows from CSV files by index or name"
}
