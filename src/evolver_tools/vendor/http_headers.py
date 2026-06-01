#!/usr/bin/env python3
"""http-headers — Inspect HTTP response headers."""
import sys

TOOL_META = {
    "name": "http-headers",
    "func": "main",
    "desc": "Inspect HTTP response headers. Usage: http-headers <url>",
}

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: http-headers <url>", file=sys.stderr)
        sys.exit(1)
    url = args[0]
    if not url.startswith("http"):
        url = "https://" + url
    try:
        import urllib.request
        req = urllib.request.Request(url, method="HEAD")
        req.add_header("User-Agent", "evolver-tools/11.0")
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"HTTP/1.1 {resp.status} {resp.reason}")
            print(f"URL: {resp.url}")
            print("--- Headers ---")
            for key, val in resp.headers.items():
                print(f"  {key}: {val}")
    except Exception as e:
        # Fallback: try GET
        try:
            import urllib.request
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "evolver-tools/11.0")
            with urllib.request.urlopen(req, timeout=15) as resp:
                print(f"HTTP/1.1 {resp.status} {resp.reason}")
                print(f"URL: {resp.url}")
                print("--- Headers ---")
                for key, val in resp.headers.items():
                    print(f"  {key}: {val}")
        except Exception as e2:
            print(f"Error: {e2}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
