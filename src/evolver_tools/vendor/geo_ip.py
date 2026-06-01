#!/usr/bin/env python3
"""geo-ip — Look up geolocation for an IP address."""
import json
import sys
import urllib.request

TOOL_META = {
    "name": "geo-ip",
    "func": "main",
    "desc": "Look up IP geolocation. Usage: geo-ip [IP address]",
}

SERVICES = [
    ("https://ipinfo.io/{}/json", lambda d: {
        "ip": d.get("ip"),
        "city": d.get("city"),
        "region": d.get("region"),
        "country": d.get("country"),
        "loc": d.get("loc"),
        "org": d.get("org"),
        "timezone": d.get("timezone"),
    }),
    ("https://ip-api.com/json/{}", lambda d: {
        "ip": d.get("query"),
        "city": d.get("city"),
        "region": d.get("regionName"),
        "country": d.get("country"),
        "lat": d.get("lat"),
        "lon": d.get("lon"),
        "org": d.get("isp"),
        "timezone": d.get("timezone"),
    }),
]

def lookup_ip(ip_addr):
    """Look up IP address geolocation."""
    for url_template, parser in SERVICES:
        url = url_template.format(ip_addr)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "evolver-tools/12.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
            result = parser(data)
            if result.get("ip"):
                return result
        except Exception:
            continue
    return None

def main():
    args = sys.argv[1:]
    ip = args[0] if args else "me"
    result = lookup_ip(ip)
    if not result:
        print(f"Could not look up: {ip}", file=sys.stderr)
        sys.exit(1)
    print(f"IP Address:   {result.get('ip', 'N/A')}")
    print(f"City:         {result.get('city', 'N/A')}")
    print(f"Region:       {result.get('region', 'N/A')}")
    print(f"Country:      {result.get('country', 'N/A')}")
    if result.get("loc"):
        print(f"Location:     {result['loc']}")
    if result.get("lat") and result.get("lon"):
        print(f"Coordinates:  {result['lat']}, {result['lon']}")
    if result.get("org"):
        print(f"ISP:          {result['org']}")
    if result.get("timezone"):
        print(f"Timezone:     {result['timezone']}")

if __name__ == "__main__":
    main()
