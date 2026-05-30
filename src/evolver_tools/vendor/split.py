#!/usr/bin/env python3
"""split — Split input into multiple files by line count.

Usage: cat file.txt | split -n 10 -o output_prefix
       split file.txt -n 100 -o chunk

Splits stdin or a file into N-line chunks.
Zero-dependency (stdlib only).
"""
import sys

def main():
    args = sys.argv[1:]
    n = 1000
    prefix = "x"
    files = []
    for i, a in enumerate(args):
        if a == '-n' and i+1 < len(args):
            n = int(args[i+1])
        elif a == '-o' and i+1 < len(args):
            prefix = args[i+1]
        elif not a.startswith('-'):
            files.append(a)
    
    if files:
        with open(files[0]) as f:
            lines = f.readlines()
    else:
        lines = sys.stdin.readlines()
    
    for i in range(0, len(lines), n):
        chunk = lines[i:i+n]
        out = f"{prefix}{i//n + 1:04d}"
        with open(out, 'w') as f:
            f.writelines(chunk)
        print(f"  wrote {out} ({len(chunk)} lines)")

TOOL_META = {
    "name": "split",
    "desc": "Split input into multiple files by line count",
    "func": "main",
}

if __name__ == '__main__':
    main()
