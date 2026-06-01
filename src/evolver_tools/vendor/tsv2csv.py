#!/usr/bin/env python3
"""tsv2csv — Convert TSV (tab-separated) to CSV format.

Usage: tsv2csv data.tsv
       tsv2csv data.tsv --delimiter '|'
       cat data.tsv | tsv2csv

Converts tab-separated values to comma-separated values.
Handles quotes, embedded commas, and newlines properly.
"""

import csv
import sys
import os

TOOL_META = {
    "name": "tsv2csv",
    "func": "main",
    "desc": "Convert TSV (tab-separated) to CSV format",
}


def main():
    args = sys.argv[1:]
    delimiter = '\t'
    files = []

    for arg in args:
        if arg in ('-h', '--help'):
            print(__doc__)
            return
        elif arg == '--delimiter' and i + 1 < len(args):
            delimiter = args[i + 1]
            i += 2
        elif arg.startswith('--delimiter='):
            delimiter = arg.split('=', 1)[1]
        elif not arg.startswith('--'):
            files.append(arg)

    # Re-parse properly
    i = 0
    files = []
    while i < len(args):
        if args[i] in ('-h', '--help'):
            print(__doc__)
            return
        elif args[i] == '--delimiter' and i + 1 < len(args):
            delimiter = args[i + 1]
            i += 2
        elif args[i].startswith('--delimiter='):
            delimiter = args[i].split('=', 1)[1]
            i += 1
        elif not args[i].startswith('--'):
            files.append(args[i])
            i += 1
        else:
            i += 1

    if files:
        for path in files:
            if not os.path.exists(path):
                print(f"Error: file not found: {path}", file=sys.stderr)
                sys.exit(1)
            with open(path, newline='', encoding='utf-8-sig') as f:
                reader = csv.reader(f, delimiter=delimiter)
                writer = csv.writer(sys.stdout)
                for row in reader:
                    writer.writerow(row)
    else:
        reader = csv.reader(sys.stdin, delimiter=delimiter)
        writer = csv.writer(sys.stdout)
        for row in reader:
            writer.writerow(row)
