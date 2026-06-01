#!/usr/bin/env python3
"""url_parser — Parse and analyze URLs."""

import sys
from urllib.parse import urlparse, parse_qs

TOOL_META = {
    "name": "url_parser",
    "func": "main",
    "desc": "Parse and analyze URLs",
}


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print("Usage: evolver url_parser <url>")
        print("       echo '<url>' | evolver url_parser")
        print()
        print("Parses a URL and shows all components.")
        return

    url = args[0] if args else sys.stdin.read().strip()
    if not url:
        print("Error: no URL provided")
        return 1

    if not url.startswith(("http://", "https://", "ftp://", "file://")):
        url = "https://" + url

    parsed = urlparse(url)

    print(f"\033[1;36m{'='*50}\033[0m")
    print(f"\033[1;33mURL Analysis\033[0m")
    print(f"\033[1;36m{'='*50}\033[0m")
    print(f"  Full URL:    {url}")
    print(f"  Scheme:      {parsed.scheme}")
    print(f"  Netloc:      {parsed.netloc}")
    print(f"  Hostname:    {parsed.hostname or ''}")
    print(f"  Port:        {parsed.port or '(default)'}")
    print(f"  Path:        {parsed.path or '/'}")
    print(f"  Params:      {parsed.params or '(none)'}")
    print(f"  Query:       {parsed.query or '(none)'}")
    print(f"  Fragment:    {parsed.fragment or '(none)'}")

    if parsed.query:
        qs = parse_qs(parsed.query)
        print(f"\n  \033[1;33mQuery Parameters ({len(qs)}):\033[0m")
        for key, values in sorted(qs.items()):
            val_str = ", ".join(values)
            print(f"    {key:<20} = {val_str}")

    # Security checks
    checks = []
    if parsed.scheme == "http":
        checks.append("\033[33m⚠ Not HTTPS\033[0m")
    if "@" in parsed.netloc:
        checks.append("\033[31m✗ Contains userinfo (phishing risk)\033[0m")
    if "localhost" in parsed.netloc or "127.0.0.1" in parsed.netloc:
        checks.append("  Localhost URL")
    if parsed.query and "redirect" in parsed.query.lower():
        checks.append("\033[33m⚠ Contains redirect parameter\033[0m")

    if checks:
        print(f"\n  \033[1;33mNotes:\033[0m")
        for c in checks:
            print(f"    {c}")


if __name__ == "__main__":
    main()
