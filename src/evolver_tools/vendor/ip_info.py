#!/usr/bin/env python3
"""ip_info — Show public IP address and geolocation info.

Usage: ip_info                 # Your public IP
       ip_info 8.8.8.8        # Lookup specific IP
       ip_info --json          # JSON output

Uses ip-api.com for geolocation data.
"""

import sys
import json
import urllib.request
import urllib.error

TOOL_META = {
    "name": "ip_info",
    "func": "main",
    "desc": "Show public IP address and geolocation info",
}


def main():
    args = sys.argv[1:]
    ip = None
    json_mode = False

    for arg in args:
        if arg in ('-h', '--help'):
            print(__doc__)
            return
        elif arg == '--json' or arg == '-j':
            json_mode = True
        elif not arg.startswith('--'):
            ip = arg
        else:
            print(f"Unknown flag: {arg}", file=sys.stderr)
            sys.exit(1)

    target = ip or ''
    url = f"http://ip-api.com/json/{target}?fields=status,message,query,country,regionName,city,zip,lat,lon,isp,org,as,timezone"

    try:
        resp = urllib.request.urlopen(url, timeout=10)
        data = json.loads(resp.read().decode())
    except urllib.error.URLError as e:
        print(f"Error: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error: invalid response from API", file=sys.stderr)
        sys.exit(1)

    if data.get('status') == 'fail':
        print(f"Error: {data.get('message', 'unknown')}", file=sys.stderr)
        sys.exit(1)

    if json_mode:
        print(json.dumps(data, indent=2))
        return

    print(f"  IP:        {data['query']}")
    print(f"  Country:   {data.get('country', 'N/A')}")
    print(f"  Region:    {data.get('regionName', 'N/A')}")
    print(f"  City:      {data.get('city', 'N/A')}")
    print(f"  ZIP:       {data.get('zip', 'N/A')}")
    print(f"  Lat/Lon:   {data.get('lat', '')}, {data.get('lon', '')}")
    print(f"  ISP:       {data.get('isp', 'N/A')}")
    print(f"  Org:       {data.get('org', 'N/A')}")
    print(f"  AS:        {data.get('as', 'N/A')}")
    print(f"  Timezone:  {data.get('timezone', 'N/A')}")
