#!/usr/bin/env python3
"""sort — Line sorting tool (alpha, numeric, reverse, unique, by column)

Like Unix sort but simpler, zero deps, cross-platform.

Usage:
    sort data.txt                    # Alphabetical sort (default)
    sort -n data.txt                 # Numeric sort
    sort -r data.txt                 # Reverse
    sort -u data.txt                 # Unique
    sort -c 2 data.txt              # Sort by column 2 (tab-separated)
    sort -c 2 -s ',' data.txt        # Sort by column 2, comma-separated
    cat data.txt | sort -n -r        # Numeric, reversed from stdin
    sort -n -u -r data.txt           # Combine flags
"""
import sys
import os
import re


def parse_args(args):
    """Parse command-line arguments."""
    opts = {
        'numeric': False,
        'reverse': False,
        'unique': False,
        'column': None,
        'separator': None,
        'ignore_case': False,
        'files': [],
        'human': False,  # human-readable numbers (1K, 2M, etc)
        'random': False,
    }
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ('-h', '--help'):
            print(__doc__.strip())
            sys.exit(0)
        elif arg == '-n':
            opts['numeric'] = True
        elif arg == '-r':
            opts['reverse'] = True
        elif arg == '-u':
            opts['unique'] = True
        elif arg == '-f' or arg == '--ignore-case':
            opts['ignore_case'] = True
        elif arg == '-R' or arg == '--random':
            opts['random'] = True
        elif arg == '--human':
            opts['human'] = True
        elif arg == '-c' or arg == '--column':
            i += 1
            if i < len(args):
                opts['column'] = int(args[i]) - 1  # Convert to 0-indexed
        elif arg == '-s' or arg == '--separator' or arg == '--sep':
            i += 1
            if i < len(args):
                opts['separator'] = args[i]
        elif arg.startswith('-'):
            # Handle combined flags like -nru
            for ch in arg[1:]:
                if ch == 'n':
                    opts['numeric'] = True
                elif ch == 'r':
                    opts['reverse'] = True
                elif ch == 'u':
                    opts['unique'] = True
                elif ch == 'f':
                    opts['ignore_case'] = True
                else:
                    print(f"Error: unknown flag '-{ch}'", file=sys.stderr)
                    sys.exit(1)
        else:
            opts['files'].append(arg)
        i += 1
    return opts


def read_lines(files):
    """Read lines from files or stdin."""
    lines = []
    if not files:
        # Read stdin
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
    return lines


def human_sort_key(val):
    """Sort key for human-readable sizes (1K, 2M, 3G, etc)."""
    suffixes = {'k': 1, 'K': 1, 'M': 2, 'G': 3, 'T': 4, 'P': 5}
    val = str(val).strip()
    if val and val[-1] in suffixes:
        num = val[:-1]
        try:
            return float(num) * (1024 ** suffixes[val[-1]])
        except ValueError:
            pass
    try:
        return float(val)
    except ValueError:
        return 0


def get_sort_key(opts):
    """Create a sort key function based on options."""
    def key_func(line):
        # Get the value to sort by
        field = line
        if opts['column'] is not None:
            sep = opts['separator'] if opts['separator'] else None
            if sep:
                parts = line.split(sep)
            else:
                parts = line.split()
            if opts['column'] < len(parts):
                field = parts[opts['column']]
            else:
                field = ''

        if opts['ignore_case']:
            field = field.lower()

        if opts['human']:
            return (0, human_sort_key(field))
        if opts['numeric']:
            try:
                return (0, float(field))
            except ValueError:
                # Extract first number
                nums = re.findall(r'-?\d+\.?\d*', field)
                if nums:
                    return (1, float(nums[0]))
                return (2, field.lower())
        return (3, field if not opts['ignore_case'] else field.lower())
    return key_func


def main():
    opts = parse_args(sys.argv[1:])
    lines = read_lines(opts['files'])

    if not lines:
        return

    # Sort
    if opts['random']:
        import random
        random.shuffle(lines)
    else:
        key_func = get_sort_key(opts)
        lines.sort(key=key_func, reverse=opts['reverse'])

    # Unique
    if opts['unique']:
        unique = []
        seen = set()
        for line in lines:
            key = line.lower() if opts['ignore_case'] else line
            if key not in seen:
                seen.add(key)
                unique.append(line)
        lines = unique

    # Output
    for line in lines:
        sys.stdout.write(line + '\n')


if __name__ == '__main__':
    main()
