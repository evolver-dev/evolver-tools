#!/usr/bin/env python3
"""time-duration — Calculate duration between dates/timestamps.

Usage: time-duration <start> <end>
       time-duration 2024-01-01 2024-12-31
       time-duration "2024-01-01 09:00" "2024-01-01 17:30"
       time-duration --now "2025-01-01"  # from now to date

Formats: YYYY-MM-DD, YYYY-MM-DD HH:MM, ISO 8601, epoch seconds
"""

import sys
from datetime import datetime, timedelta


def _parse(s):
    s = s.strip()
    # Epoch
    try:
        return datetime.fromtimestamp(int(s))
    except (ValueError, OSError):
        pass
    # ISO formats
    for fmt in [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d",
        "%Y%m%d",
    ]:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse time: {s}")


def main():
    args = sys.argv[1:]
    if '-h' in args or '--help' in args:
        print(__doc__)
        return
    if not args:
        print(__doc__)
        return
    try:
        now = datetime.now()
        if '--now' in args:
            idx = args.index('--now')
            if idx + 1 < len(args):
                end = _parse(args[idx + 1])
            else:
                end = now
            start = now
        elif len(args) >= 2:
            start = _parse(args[0])
            end = _parse(args[1])
        else:
            start = _parse(args[0])
            end = now
        delta = end - start
        total_secs = int(delta.total_seconds())
        days, rem = divmod(abs(total_secs), 86400)
        hours, rem = divmod(rem, 3600)
        mins, secs = divmod(rem, 60)
        sign = "-" if total_secs < 0 else ""
        print(f"Start: {start}")
        print(f"End:   {end}")
        print(f"Duration: {sign}{days}d {hours:02d}:{mins:02d}:{secs:02d}")
        print(f"Total:    {total_secs}s")
        print(f"          {abs(total_secs)/3600:.2f}h")
        print(f"          {abs(total_secs)/86400:.2f}d")
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


TOOL_META = {
    "name": "time-duration",
    "func": "main",
    "desc": "Calculate duration between dates/timestamps in multiple formats"
}
