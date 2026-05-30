#!/usr/bin/env python3
"""
GeoIP location lookup using ip-api.com (free, no API key required).

Queries the public ip-api.com API to determine the geographic location
of an IP address. Uses only Python stdlib (urllib, json, sys) —
zero external dependencies.

Usage:
    python -m evolver_tools.vendor.ip_location
    python -m evolver_tools.vendor.ip_location 8.8.8.8
    python -m evolver_tools.vendor.ip_location --json 1.1.1.1
"""

import argparse
import json
import sys
import urllib.error
import urllib.request

TOOL_META = {
    'name': 'ip-location',
    'func': 'main',
    'desc': 'GeoIP location lookup (ip-api.com)',
}

API_BASE = 'http://ip-api.com/json/'


def _api_get(ip: str) -> dict:
    """Query ip-api.com for the given IP and return parsed JSON."""
    url = API_BASE + ip
    req = urllib.request.Request(url, headers={'User-Agent': 'ip-location/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        msg = e.read().decode('utf-8', errors='replace') if e.fp else ''
        print(f'HTTP error {e.code}: {msg}', file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f'Network error: {e.reason}', file=sys.stderr)
        sys.exit(1)
    except (json.JSONDecodeError, OSError, ValueError) as e:
        print(f'Error parsing response: {e}', file=sys.stderr)
        sys.exit(1)


def lookup(ip: str, as_json: bool = False) -> None:
    """Look up an IP address and display the result."""
    data = _api_get(ip)

    if data.get('status') != 'success':
        msg = data.get('message', 'unknown error')
        print(f'Lookup failed for "{ip}": {msg}', file=sys.stderr)
        sys.exit(1)

    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    fields = {
        'IP': data.get('query', ip),
        'Country': data.get('country', ''),
        'Country Code': data.get('countryCode', ''),
        'Region': data.get('regionName', ''),
        'Region Code': data.get('region', ''),
        'City': data.get('city', ''),
        'ZIP': data.get('zip', ''),
        'Latitude': str(data.get('lat', '')),
        'Longitude': str(data.get('lon', '')),
        'Timezone': data.get('timezone', ''),
        'ISP': data.get('isp', ''),
        'Organization': data.get('org', ''),
        'AS': data.get('as', ''),
    }

    max_key_len = max(len(k) for k in fields)
    for key, val in fields.items():
        if val:
            print(f'{key:>{max_key_len + 1}}  {val}')


def main() -> None:
    """Parse arguments and run the lookup."""
    parser = argparse.ArgumentParser(
        description='GeoIP location lookup via ip-api.com',
    )
    parser.add_argument(
        'ip',
        nargs='?',
        default='',
        help='IP address to look up (default: auto, queries your own IP)',
    )
    parser.add_argument(
        '--json',
        action='store_true',
        dest='as_json',
        help='Output raw JSON response',
    )
    args = parser.parse_args()

    ip = args.ip if args.ip else ''
    lookup(ip, as_json=args.as_json)


if __name__ == '__main__':
    main()
