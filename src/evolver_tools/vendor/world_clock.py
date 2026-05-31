#!/usr/bin/env python3
"""world-clock — Show current time in multiple timezones.

Usage: world-clock
       world-clock Asia/Tokyo America/New_York
       world-clock --list

Zero-dependency (stdlib only — uses datetime + zoneinfo).
Note: zoneinfo is available in Python 3.9+.
"""
import sys
import datetime


def main():
    args = sys.argv[1:]

    if '-h' in args or '--help' in args:
        print(__doc__)
        return

    # Try zoneinfo (Python 3.9+)
    try:
        import zoneinfo
    except ImportError:
        import pytz as _unused  # fallback hint
        print('Error: zoneinfo module required (Python 3.9+)', file=sys.stderr)
        sys.exit(1)

    if '--list' in args:
        print('Available timezones (sample):')
        znames = sorted(zoneinfo.available_timezones())
        # Show common ones
        common = [z for z in znames if '/' in z and not z.startswith('Etc/')]
        for z in common[:40]:
            print(f'  {z}')
        print(f'  ... {len(common)} total available')
        return

    # Default zones if none specified
    zones = args if args else [
        'UTC',
        'America/New_York',
        'America/Chicago',
        'America/Denver',
        'America/Los_Angeles',
        'Europe/London',
        'Europe/Berlin',
        'Europe/Moscow',
        'Asia/Shanghai',
        'Asia/Tokyo',
        'Asia/Kolkata',
        'Australia/Sydney',
        'Pacific/Auckland',
    ]

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    print(f'Reference: {now_utc.strftime("%Y-%m-%d %H:%M:%S")} UTC')
    print()

    width = max(len(z) for z in zones) + 2
    for zone_name in zones:
        try:
            tz = zoneinfo.ZoneInfo(zone_name)
            dt = now_utc.astimezone(tz)
            offset = dt.strftime('%z')
            formatted = dt.strftime('%Y-%m-%d %H:%M:%S')
            print(f'  {zone_name:<{width}} {formatted}  (UTC{offset})')
        except zoneinfo.ZoneInfoNotFoundError:
            print(f'  {zone_name:<{width}} [unknown timezone]')


TOOL_META = {
    "name": "world-clock",
    "func": "main",
    "desc": "Show current time in multiple timezones",
}

if __name__ == '__main__':
    main()
