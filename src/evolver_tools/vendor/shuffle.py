#!/usr/bin/env python3
"""shuffle — Randomize lines from stdin.

Usage: cat file.txt | shuffle [--seed=<n>]
       echo "a\nb\nc" | shuffle

Shuffles input lines using Fisher-Yates algorithm.
Zero-dependency (stdlib only).
"""
import sys, random

def main():
    seed = None
    args = sys.argv[1:]
    for a in args:
        if a.startswith('--seed='):
            seed = int(a.split('=', 1)[1])
    lines = sys.stdin.read().splitlines(keepends=False)
    if not lines:
        return
    if seed is not None:
        random.seed(seed)
    random.shuffle(lines)
    sys.stdout.write('\n'.join(lines))
    if sys.stdin.isatty():
        sys.stdout.write('\n')

if __name__ == '__main__':
    main()
