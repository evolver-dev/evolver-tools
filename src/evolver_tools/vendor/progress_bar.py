#!/usr/bin/env python3
"""progress-bar — Show progress bar in terminal.

Usage: progress-bar --total=100 --current=42
       command | progress-bar --total=100

Displays a progress bar with percentage, bar, and optional ETA.
Zero-dependency (stdlib only).
"""
import sys, time

def render_bar(current, total, width=30):
    pct = current / total if total > 0 else 0
    filled = int(pct * width)
    bar = '█' * filled + '░' * (width - filled)
    return f"|{bar}| {int(pct*100):3d}%"

def main():
    args = sys.argv[1:]
    total = 100
    for i, a in enumerate(args):
        if a.startswith('--total='):
            total = int(a.split('=',1)[1])
    
    if sys.stdin.isatty():
        # Direct mode: show a single bar
        current = 0
        for a in args:
            if a.startswith('--current='):
                current = int(a.split('=',1)[1])
        print(f"\r{render_bar(current, total)}", end='')
        if current == total:
            print()
    else:
        # Pipe mode: count lines as progress
        lines = sys.stdin.readlines()
        n = len(lines)
        for i, line in enumerate(lines):
            sys.stdout.write(line)
            pct = (i + 1) / n * 100
            bar = render_bar(i + 1, n)
            print(f"\r{bar}", end='', file=sys.stderr)
        print(file=sys.stderr)


# === Auto-registration metadata ===
TOOL_META = {
    "name": "progress-bar",
    "func": "main",
    "desc": 'Animated terminal progress bar',
}

if __name__ == '__main__':
    main()
