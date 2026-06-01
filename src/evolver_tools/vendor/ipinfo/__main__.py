
def main():
    import urllib.request
    import json
    import sys
    
    try:
        resp = urllib.request.urlopen("http://ip-api.com/json/", timeout=5)
        data = json.loads(resp.read().decode())
        if data.get("status") == "fail":
            # fallback to ipify
            ip = urllib.request.urlopen("https://api.ipify.org?format=json", timeout=5).read().decode()
            data2 = json.loads(ip)
            print(f"IP: {data2.get('ip', 'unknown')}")
            print("Location: (geo lookup failed)")
        else:
            print(f"IP:       {data.get('query', '?')}")
            print(f"Country:  {data.get('country', '?')}")
            print(f"Region:   {data.get('regionName', '?')}")
            print(f"City:     {data.get('city', '?')}")
            print(f"ISP:      {data.get('isp', '?')}")
            print(f"Org:      {data.get('org', '?')}")
            print(f"AS:       {data.get('as', '?')}")
            print(f"Lat/Lon:  {data.get('lat', '?')}, {data.get('lon', '?')}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
