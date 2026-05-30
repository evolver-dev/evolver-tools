#!/usr/bin/env python3
"""weather-cli — Weather forecast from wttr.in.

Usage: weather-cli          — current location
       weather-cli London   — specific city
       weather-cli Beijing
       weather-cli --json Beijing  — JSON output

Zero-dependency (stdlib only, uses urllib).
"""
import sys, json
try:
    from urllib.request import urlopen, Request
except ImportError:
    from urllib2 import urlopen, Request

def main():
    args = sys.argv[1:]
    city = ''
    fmt = '1'
    json_mode = False
    for a in args:
        if a == '--json':
            fmt = 'j'
            json_mode = True
        elif not a.startswith('-'):
            city = a
    if city:
        url = f'https://wttr.in/{city}?{fmt}'
    else:
        url = f'https://wttr.in?{fmt}'
    try:
        req = Request(url, headers={'User-Agent': 'curl/7.68'})
        data = urlopen(req, timeout=10).read().decode('utf-8')
        if json_mode:
            parsed = json.loads(data)
            print(json.dumps(parsed, indent=2, ensure_ascii=False))
        else:
            print(data)
    except Exception as e:
        print(f"Error fetching weather: {e}", file=sys.stderr)
        sys.exit(1)


# === Auto-registration metadata ===
TOOL_META = {
    "name": "weather-cli",
    "func": "main",
    "desc": 'Weather forecast from wttr.in',
}

if __name__ == '__main__':
    main()
