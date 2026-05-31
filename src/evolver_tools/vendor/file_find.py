#!/usr/bin/env python3
"""file_find — Find files by name pattern with recursive search.

Usage: file_find *.txt              # Find all .txt files
       file_find config* --dir .    # In current dir
       file_find test_*.py --max 10 # Limit results
       file_find Dockerfile         # Exact name match

Lightweight alternative to 'find' with simpler syntax.
Uses fnmatch pattern matching. Zero dependencies.
"""

import os
import sys
import fnmatch

TOOL_META = {
    "name": "file_find",
    "func": "main",
    "desc": "Find files by name pattern with recursive search",
}


def main():
    args = sys.argv[1:]
    if not args or args[0] in ('-h', '--help'):
        print(__doc__)
        return

    pattern = None
    search_dir = os.getcwd()
    max_results = 0
    case_insensitive = False
    type_filter = None  # 'f' or 'd'

    i = 0
    while i < len(args):
        if args[i] == '--dir' and i + 1 < len(args):
            search_dir = os.path.abspath(args[i + 1])
            i += 2
        elif args[i] == '--max' and i + 1 < len(args):
            max_results = int(args[i + 1])
            i += 2
        elif args[i] == '--type' and i + 1 < len(args):
            type_filter = args[i + 1]
            i += 2
        elif args[i] == '--ignore-case' or args[i] == '-i':
            case_insensitive = True
            i += 1
        elif not args[i].startswith('--'):
            pattern = args[i]
            i += 1
        else:
            i += 1

    if not pattern:
        print("Error: no pattern specified", file=sys.stderr)
        sys.exit(1)

    if not os.path.isdir(search_dir):
        print(f"Error: directory not found: {search_dir}", file=sys.stderr)
        sys.exit(1)

    count = 0
    for root, dirs, files in os.walk(search_dir):
        # Skip hidden dirs by default
        dirs[:] = [d for d in dirs if not d.startswith('.')]

        targets = []
        if type_filter in (None, 'f'):
            targets.extend(files)
        if type_filter in (None, 'd'):
            targets.extend(dirs)

        for name in targets:
            matched = False
            if case_insensitive:
                matched = fnmatch.fnmatch(name.lower(), pattern.lower())
            else:
                matched = fnmatch.fnmatch(name, pattern)

            if matched:
                path = os.path.join(root, name)
                print(path)
                count += 1
                if max_results and count >= max_results:
                    print(f"--- {count} results (max: {max_results}) ---")
                    return

    if count == 0:
        print(f"No files matching '{pattern}' in {search_dir}")
