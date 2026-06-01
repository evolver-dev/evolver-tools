#!/usr/bin/env python3
"""whois-lookup — WHOIS domain lookup."""
import subprocess
import sys

TOOL_META = {
    "name": "whois-lookup",
    "func": "main",
    "desc": "WHOIS domain lookup. Usage: whois-lookup <domain>",
}

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: whois-lookup <domain>", file=sys.stderr)
        sys.exit(1)
    domain = args[0]
    # Try whois command first
    try:
        result = subprocess.run(["whois", domain], capture_output=True, text=True, timeout=15)
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.split("\n")
            # Filter common useful fields
            useful = [l for l in lines if any(k in l.lower() for k in [
                "domain name", "registrar", "creation date", "expir", "name server",
                "registrant", "admin", "tech", "status", "dnssec"
            ])]
            if useful:
                for l in useful:
                    print(l)
            else:
                # Just show first 30 lines
                for l in lines[:30]:
                    print(l)
                if len(lines) > 30:
                    print(f"... ({len(lines) - 30} more lines)")
            return
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    # Fallback: use RDAP (whois-like HTTP API)
    try:
        import urllib.request
        import json
        url = f"https://rdap.verisign.com/com/v1/domain/{domain}"
        req = urllib.request.Request(url, headers={"User-Agent": "evolver-tools/11.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        # Extract useful info
        if "events" in data:
            for ev in data["events"]:
                print(f"{ev['eventAction']:<20} {ev['eventDate']}")
        if "entities" in data:
            for ent in data["entities"]:
                if "vcardArray" in ent:
                    for vcard in ent["vcardArray"][1]:
                        if vcard[0] == "fn":
                            print(f"Registrant:            {vcard[3]}")
        print(f"\nFull RDAP response available at: {url}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        print("Install the 'whois' system package: apt install whois", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
