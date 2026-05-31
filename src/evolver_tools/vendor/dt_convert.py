#!/usr/bin/env python3
"""dt — Date/time format conversions, timestamps, timezone offsets.

Usage:
  dt now           — current time in ISO format
  dt utcnow        — current UTC time in ISO format
  dt format <fmt>  — current time formatted (strftime)
  dt ts [epoch_s]  — convert epoch seconds to ISO
  dt parse "str"   — try to parse a date string

All output in local timezone unless --utc specified.
Zero-dependency (stdlib only).
"""

import sys
import time
import re
from datetime import datetime, timezone, timedelta

# Common date patterns
PATTERNS = [
    ("%Y-%m-%dT%H:%M:%S", r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'),
    ("%Y-%m-%d %H:%M:%S", r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'),
    ("%Y-%m-%d", r'\d{4}-\d{2}-\d{2}'),
    ("%m/%d/%Y", r'\d{2}/\d{2}/\d{4}'),
    ("%d/%m/%Y", r'\d{2}/\d{2}/\d{4}'),
    ("%Y/%m/%d", r'\d{4}/\d{2}/\d{2}'),
    ("%H:%M:%S", r'\d{2}:\d{2}:\d{2}'),
]


def try_parse(s):
    s = s.strip().strip('"').strip("'")
    for fmt, pat in PATTERNS:
        if re.fullmatch(pat, s):
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                pass
    return None


def now_str():
    return datetime.now().isoformat(timespec='seconds')


def utcnow_str():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def from_epoch(sec, utc=False):
    try:
        if utc:
            dt = datetime.fromtimestamp(float(sec), tz=timezone.utc)
        else:
            dt = datetime.fromtimestamp(float(sec))
        return dt.isoformat(timespec='seconds')
    except (ValueError, OSError):
        return None


def main():
    args = sys.argv[1:]
    utc = '--utc' in args
    if utc:
        args.remove('--utc')

    if not args or args[0] == 'now':
        print(utcnow_str() if utc else now_str())
        return

    cmd = args[0]

    if cmd == 'utcnow':
        print(utcnow_str())
        return

    if cmd == 'ts':
        sec = args[1] if len(args) > 1 else str(time.time())
        result = from_epoch(sec, utc)
        if result:
            print(result)
        else:
            print(f"Invalid timestamp: {sec}", file=sys.stderr)
            sys.exit(1)
        return

    if cmd == 'format':
        fmt = args[1] if len(args) > 1 else '%Y-%m-%d %H:%M:%S'
        if utc:
            print(datetime.now(timezone.utc).strftime(fmt))
        else:
            print(datetime.now().strftime(fmt))
        return

    if cmd == 'parse':
        if len(args) < 2:
            print("Usage: dt parse \"date string\"", file=sys.stderr)
            sys.exit(1)
        result = try_parse(args[1])
        if result:
            print(f"Parsed: {result.isoformat(timespec='seconds')}")
        else:
            print(f"Could not parse: {args[1]}", file=sys.stderr)
            sys.exit(1)
        return

    # If it looks like a timestamp, treat it as one
    if re.match(r'^\d+(\.\d+)?$', cmd):
        result = from_epoch(cmd, utc)
        if result:
            print(result)
            return

    # Show help
    print(__doc__.strip())
    if cmd not in ('now', 'utcnow', 'ts', 'format', 'parse', '--help', '-h'):
        print(f"\nUnknown command: {cmd}", file=sys.stderr)
        sys.exit(1)



# === Auto-registration metadata ===
TOOL_META = {
    "name": "dt",
    "func": "main",
    "desc": 'Date/time format converter (timestamps, timezones)',
}

if __name__ == '__main__':
    main()
