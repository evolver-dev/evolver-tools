#!/usr/bin/env python3
"""env-diff — Compare two .env files."""
import os
import sys

TOOL_META = {
    "name": "env-diff",
    "func": "main",
    "desc": "Compare .env files. Usage: env-diff <file1.env> <file2.env>",
}

def parse_env(filepath):
    vars = {}
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                vars[key.strip()] = val.strip().strip("\"'")
    return vars

def main():
    args = sys.argv[1:]
    if len(args) < 2 or args[0] in ("-h", "--help"):
        print("Usage: env-diff <file1.env> <file2.env>")
        return
    f1, f2 = args[0], args[1]
    for f in [f1, f2]:
        if not os.path.exists(f):
            print(f"File not found: {f}", file=sys.stderr)
            sys.exit(1)
    env1 = parse_env(f1)
    env2 = parse_env(f2)
    keys1 = set(env1.keys())
    keys2 = set(env2.keys())
    only_in_1 = keys1 - keys2
    only_in_2 = keys2 - keys1
    common = keys1 & keys2
    different = {k for k in common if env1[k] != env2[k]}
    print(f"Comparison: {os.path.basename(f1)} vs {os.path.basename(f2)}")
    print(f"Total vars: {len(keys1)} → {len(keys2)}")
    print()
    if only_in_1:
        print(f"Only in {os.path.basename(f1)} ({len(only_in_1)}):")
        for k in sorted(only_in_1):
            print(f"  + {k}={env1[k]}")
        print()
    if only_in_2:
        print(f"Only in {os.path.basename(f2)} ({len(only_in_2)}):")
        for k in sorted(only_in_2):
            print(f"  + {k}={env2[k]}")
        print()
    if different:
        print(f"Different values ({len(different)}):")
        for k in sorted(different):
            print(f"  * {k}")
            print(f"    - {env1[k]}")
            print(f"    + {env2[k]}")
        print()
    if not only_in_1 and not only_in_2 and not different:
        print("✓ Files are identical")
    else:
        changed = len(only_in_1) + len(only_in_2) + len(different)
        print(f"Summary: {changed} difference(s)")

if __name__ == "__main__":
    main()
