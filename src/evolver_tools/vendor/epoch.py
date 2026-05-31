#!/usr/bin/env python3
"""epoch — Unix timestamp / human date converter.

Usage: epoch                     # -> current Unix time
       epoch now                 # -> current date
       epoch 1717171717          # -> human-readable
       epoch "2026-06-01 12:00"  # -> Unix timestamp
       epoch --utc               # UTC mode

Supports various input formats including ISO 8601.
Zero-dependency (stdlib only).
"""

import sys
from datetime import datetime, timezone


def parse_date(text):
    """Try to parse a date string, return datetime or None."""
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%d',
        '%Y/%m/%d %H:%M:%S',
        '%Y/%m/%d %H:%M',
        '%Y/%m/%d',
        '%m/%d/%Y %H:%M:%S',
        '%m/%d/%Y %H:%M',
        '%m/%d/%Y',
    ]
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def main():
    args = sys.argv[1:]
    utc_mode = '-u' in args or '--utc' in args
    args = [a for a in args if a not in ('-u', '--utc')]

    if '-h' in args or '--help' in args:
        print(__doc__)
        return

    if not args or args[0] == 'now':
        now = datetime.now(timezone.utc if utc_mode else None)
        ts = int(now.timestamp())
        if not args:
            print(ts)
        else:
            print(f"Unix:    {ts}")
            print(f"Local:   {now.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"UTC:     {datetime.fromtimestamp(ts, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
        return

    text = ' '.join(args)

    # Try as Unix timestamp
    try:
        ts = int(text)
        dt_local = datetime.fromtimestamp(ts)
        dt_utc = datetime.fromtimestamp(ts, tz=timezone.utc)
        print(f"Unix:    {ts}")
        print(f"Local:   {dt_local.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"UTC:     {dt_utc.strftime('%Y-%m-%d %H:%M:%S')}")
        return
    except ValueError:
        pass

    # Try as date string
    dt = parse_date(text)
    if dt:
        ts = int(dt.replace(tzinfo=timezone.utc).timestamp())
        print(f"Date:    {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Unix:    {ts}")
        return

    print(f"Error: cannot parse '{text}'", file=sys.stderr)
    sys.exit(1)


# === Auto-registration metadata ===
TOOL_META = {
    "name": "epoch",
    "func": "main",
    "desc": 'Unix timestamp / human date converter',
}

if __name__ == '__main__':
    main()
