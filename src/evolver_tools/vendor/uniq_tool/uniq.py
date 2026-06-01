#!/usr/bin/env python3
"""uniq — Unique line filter (like Unix uniq, but smarter)

Filter adjacent or global duplicate lines. Supports counting, case-insensitive,
and full-deduplication (not just adjacent).

Usage:
    uniq data.txt                       # Adjacent uniquify (like uniq)
    uniq -u data.txt                    # Global uniquify (remove ALL duplicates globally)
    uniq -c data.txt                    # Count occurrences per unique line
    uniq -i data.txt                    # Case-insensitive
    uniq -d data.txt                    # Only show duplicate lines
    cat data.txt | uniq                 # Stdin mode
"""
import sys
import os


def main():
    args = sys.argv[1:]

    if not args or (len(args) == 1 and args[0] in ('-h', '--help')):
        print(__doc__.strip())
        return

    global_mode = False
    count_mode = False
    dups_only = False
    ignore_case = False
    files = []

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == '-u':
            global_mode = True
        elif arg == '-c':
            count_mode = True
        elif arg == '-d':
            dups_only = True
        elif arg == '-i' or arg == '--ignore-case':
            ignore_case = True
        elif arg.startswith('-'):
            for ch in arg[1:]:
                if ch == 'u':
                    global_mode = True
                elif ch == 'c':
                    count_mode = True
                elif ch == 'd':
                    dups_only = True
                elif ch == 'i':
                    ignore_case = True
                else:
                    print(f"Error: unknown flag '{ch}'", file=sys.stderr)
                    sys.exit(1)
        else:
            files.append(arg)
        i += 1

    # Read lines
    lines = []
    if not files:
        for line in sys.stdin:
            lines.append(line.rstrip('\n').rstrip('\r'))
    else:
        for filepath in files:
            if not os.path.isfile(filepath):
                print(f"Error: file not found: {filepath}", file=sys.stderr)
                sys.exit(1)
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    lines.append(line.rstrip('\n').rstrip('\r'))

    if not lines:
        return

    if global_mode:
        # Global dedup (remove all duplicates)
        seen = {}
        for line in lines:
            key = line.lower() if ignore_case else line
            seen[key] = seen.get(key, 0) + 1

        if dups_only:
            output = {k: v for k, v in seen.items() if v > 1}
        else:
            output = seen

        if count_mode:
            for line_text, count in output.items():
                print(f"{count:>7} {line_text}")
        else:
            for line_text in output:
                print(line_text)
    else:
        # Adjacent uniquify (like classic uniq)
        result = []
        prev = None
        counts = {}

        for line in lines:
            key = line.lower() if ignore_case else line
            if key != prev:
                if prev is not None:
                    if count_mode:
                        result.append((prev_original, counts[prev]))
                    else:
                        if not dups_only or counts[prev] > 1:
                            result.append(prev_original)
                prev = key
                prev_original = line
                counts[key] = 1
            else:
                counts[key] = counts.get(key, 0) + 1

        # Last group
        if prev is not None:
            if dups_only and counts[prev] <= 1:
                pass
            elif count_mode:
                result.append((prev_original, counts[prev]))
            else:
                result.append(prev_original)

        if count_mode:
            for line_text, count in result:
                print(f"{count:>7} {line_text}")
        else:
            for line_text in result:
                print(line_text)


if __name__ == '__main__':
    main()
