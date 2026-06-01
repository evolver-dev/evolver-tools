#!/usr/bin/env python3
"""diff_files — Line-by-line file comparison.

Usage: diff_files file1.txt file2.txt
       diff_files file1.txt file2.txt --context 3
       diff_files file1.txt file2.txt --brief

Simple diff tool. Shows added/removed lines with +/- markers.
Zero external dependencies (pure Python difflib).
"""

import difflib
import sys
import os

TOOL_META = {
    "name": "diff_files",
    "func": "main",
    "desc": "Line-by-line file comparison",
}


def main():
    args = sys.argv[1:]
    context = 3
    brief = False
    files = []

    i = 0
    while i < len(args):
        if args[i] == '--context' and i + 1 < len(args):
            context = int(args[i + 1])
            i += 2
        elif args[i] == '--brief' or args[i] == '-q':
            brief = True
            i += 1
        elif args[i] in ('-h', '--help'):
            print(__doc__)
            return
        else:
            files.append(args[i])
            i += 1

    if len(files) != 2:
        print("Error: need exactly 2 files", file=sys.stderr)
        print(__doc__)
        sys.exit(1)

    file1, file2 = files
    for f in (file1, file2):
        if not os.path.exists(f):
            print(f"Error: file not found: {f}", file=sys.stderr)
            sys.exit(1)

    with open(file1) as f:
        lines1 = f.readlines()
    with open(file2) as f:
        lines2 = f.readlines()

    if brief:
        if lines1 != lines2:
            print(f"Files {file1} and {file2} differ")
        else:
            print(f"Files {file1} and {file2} are identical")
        return

    diff = difflib.unified_diff(
        lines1, lines2,
        fromfile=file1, tofile=file2,
        n=context
    )

    output = list(diff)
    if not output:
        print("Files are identical.")
        return

    for line in output:
        if line.startswith('+') and not line.startswith('+++'):
            sys.stdout.write(f'\033[32m{line}\033[0m')
        elif line.startswith('-') and not line.startswith('---'):
            sys.stdout.write(f'\033[31m{line}\033[0m')
        elif line.startswith('@@'):
            sys.stdout.write(f'\033[36m{line}\033[0m')
        else:
            sys.stdout.write(line)
