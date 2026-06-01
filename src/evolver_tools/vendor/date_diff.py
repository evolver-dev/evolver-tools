#!/usr/bin/env python3
"""date_diff — Calculate date/time differences.

Usage: date_diff 2026-01-01 2026-06-01
       date_diff 2026-01-01 2026-06-01 --unit hours
       date_diff now "2026-12-25"
       date_diff "2026-01-01 09:00" "2026-01-01 17:30" --unit minutes

Show difference in days, hours, minutes, or seconds between two dates.
Accepts ISO 8601 dates, 'now', and datetime strings.
"""

import sys
from datetime import datetime

TOOL_META = {
    "name": "date_diff",
    "func": "main",
    "desc": "Calculate date/time differences",
}

def parse_date(s):
    if s.lower() == 'now':
        return datetime.now()
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d',
                '%Y/%m/%d %H:%M:%S', '%Y/%m/%d %H:%M', '%Y/%m/%d',
                '%m/%d/%Y', '%d/%m/%Y'):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {s}")


def main():
    args = sys.argv[1:]
    if not args or args[0] in ('-h', '--help'):
        print(__doc__)
        return

    unit = 'days'
    date_strs = []

    i = 0
    while i < len(args):
        if args[i] == '--unit' and i + 1 < len(args):
            unit = args[i + 1].lower()
            i += 2
        elif args[i].startswith('--'):
            print(f"Unknown flag: {args[i]}", file=sys.stderr)
            sys.exit(1)
        else:
            date_strs.append(args[i])
            i += 1

    if len(date_strs) < 2:
        print("Error: need two dates", file=sys.stderr)
        sys.exit(1)

    try:
        d1 = parse_date(date_strs[0])
        d2 = parse_date(date_strs[1])
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    delta = abs(d2 - d1)
    total_seconds = delta.total_seconds()

    if unit in ('days', 'day', 'd'):
        result = total_seconds / 86400
        label = 'days'
    elif unit in ('hours', 'hour', 'h'):
        result = total_seconds / 3600
        label = 'hours'
    elif unit in ('minutes', 'minute', 'min', 'm'):
        result = total_seconds / 60
        label = 'minutes'
    elif unit in ('seconds', 'second', 'sec', 's'):
        result = total_seconds
        label = 'seconds'
    elif unit in ('weeks', 'week', 'w'):
        result = total_seconds / 604800
        label = 'weeks'
    elif unit in ('months', 'month'):
        # Approximate
        result = total_seconds / (86400 * 30.44)
        label = 'months'
    elif unit in ('years', 'year', 'y'):
        result = total_seconds / (86400 * 365.25)
        label = 'years'
    else:
        print(f"Error: unknown unit: {unit}", file=sys.stderr)
        sys.exit(1)

    if result == int(result):
        print(f"{int(result)} {label}")
    else:
        print(f"{result:.2f} {label}")
