#!/usr/bin/env python3
"""join — Join lines with delimiter.

Usage: ls | join ,
       cat file.txt | join -s " | "

Joins all input lines with a separator.
Zero-dependency (stdlib only).
"""
import sys

def main():
    delim = ' '
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a in ('-s', '--sep', '--delim') and i+1 < len(args):
            delim = args[i+1]
        elif a.startswith('-s'):
            delim = a[2:]
    lines = sys.stdin.read().splitlines(keepends=False)
    sys.stdout.write(delim.join(lines))

if __name__ == '__main__':
    main()
