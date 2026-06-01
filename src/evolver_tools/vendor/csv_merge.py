#!/usr/bin/env python3
"""csv_merge — Merge multiple CSV files by a common column.

Usage: csv_merge file1.csv file2.csv --on id
       csv_merge file1.csv file2.csv --on id --how outer
       csv_merge *.csv --on user_id --output merged.csv

Joins CSV files on a common key column, like SQL JOIN.
Supports inner, left, and outer joins.
Zero external dependencies.
"""

import csv
import sys
import os
from collections import OrderedDict

TOOL_META = {
    "name": "csv_merge",
    "func": "main",
    "desc": "Merge CSV files by common column (inner/left/outer join)",
}

def load_csv(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows:
        return [], []
    return rows, list(rows[0].keys())


def main():
    args = sys.argv[1:]
    if not args or args[0] in ('-h', '--help'):
        print(__doc__)
        return

    # Parse --on, --how, --output
    on_col = None
    how = 'inner'
    output = None
    files = []

    i = 0
    while i < len(args):
        if args[i] == '--on' and i + 1 < len(args):
            on_col = args[i + 1]
            i += 2
        elif args[i] == '--how' and i + 1 < len(args):
            how = args[i + 1].lower()
            i += 2
        elif args[i] == '--output' and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        else:
            files.append(args[i])
            i += 1

    if len(files) < 2:
        print("Error: need at least 2 CSV files", file=sys.stderr)
        sys.exit(1)

    if not on_col:
        print("Error: --on <column> required", file=sys.stderr)
        sys.exit(1)

    # Load all CSVs
    tables = []
    for f in files:
        if not os.path.exists(f):
            print(f"Error: file not found: {f}", file=sys.stderr)
            sys.exit(1)
        rows, cols = load_csv(f)
        tables.append((os.path.basename(f), rows, cols))

    # Build lookup from first file
    lookup = {}
    for row in tables[0][1]:
        key = row.get(on_col, '')
        lookup[key] = row

    # Merge subsequent files
    merged = []
    all_cols_set = OrderedDict()
    for t in tables:
        for c in t[2]:
            all_cols_set[c] = True

    all_cols = list(all_cols_set.keys())

    if how == 'inner':
        for t in tables[1:]:
            for row in t[1]:
                key = row.get(on_col, '')
                if key in lookup:
                    merged_row = OrderedDict()
                    for c in all_cols:
                        merged_row[c] = lookup[key].get(c, '') or row.get(c, '')
                    merged.append(merged_row)
        # For inner, merge first two then subsequent
        if len(tables) > 2:
            # Re-merge with remaining tables
            temp = merged
            for t in tables[2:]:
                merged2 = []
                t_lookup = {r.get(on_col, ''): r for r in t[1]}
                for row in temp:
                    key = row.get(on_col, '')
                    if key in t_lookup:
                        merged_row = OrderedDict(row)
                        for c in t_lookup[key]:
                            if c != on_col and c not in merged_row:
                                merged_row[c] = t_lookup[key][c]
                        merged2.append(merged_row)
                temp = merged2
            merged = temp
    elif how == 'left':
        merged = list(lookup.values())
        for t in tables[1:]:
            t_lookup = {r.get(on_col, ''): r for r in t[1]}
            for row in merged:
                key = row.get(on_col, '')
                if key in t_lookup:
                    for c, v in t_lookup[key].items():
                        if c != on_col and c not in row:
                            row[c] = v
    elif how == 'outer':
        all_keys = set()
        for t in tables:
            for r in t[1]:
                all_keys.add(r.get(on_col, ''))
        key_rows = {}
        for t in tables:
            for r in t[1]:
                k = r.get(on_col, '')
                if k not in key_rows:
                    key_rows[k] = OrderedDict()
                    key_rows[k][on_col] = k
                for c, v in r.items():
                    if c != on_col and v:
                        key_rows[k][c] = v
        merged = list(key_rows.values())
    else:
        print(f"Error: unknown join type: {how} (use inner/left/outer)", file=sys.stderr)
        sys.exit(1)

    # Write output
    if output:
        with open(output, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(all_cols_set.keys()))
            writer.writeheader()
            writer.writerows(merged)
        print(f"Merged {len(merged)} rows -> {output}")
    else:
        writer = csv.DictWriter(sys.stdout, fieldnames=list(all_cols_set.keys()))
        writer.writeheader()
        writer.writerows(merged)
