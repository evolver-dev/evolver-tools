#!/usr/bin/env python3
"""dns-lookup — DNS lookup tool."""
import sys

TOOL_META = {
    "name": "dns-lookup",
    "func": "main",
    "desc": "DNS lookup tool. Usage: dns-lookup <domain> [--type A|AAAA|MX|TXT|NS|CNAME|SOA]",
}

RECORD_TYPES = {
    "A": "A",
    "AAAA": "AAAA",
    "MX": "MX",
    "TXT": "TXT",
    "NS": "NS",
    "CNAME": "CNAME",
    "SOA": "SOA",
    "all": None,
}

def resolve_socket(hostname, qtype="A"):
    """Use Python's socket module for basic DNS resolution."""
    import socket
    try:
        if qtype == "A":
            result = socket.getaddrinfo(hostname, None, socket.AF_INET)
            addresses = set()
            for r in result:
                addresses.add(r[4][0])
            return list(addresses), f"A records for {hostname}"
        elif qtype == "AAAA":
            result = socket.getaddrinfo(hostname, None, socket.AF_INET6)
            addresses = set()
            for r in result:
                addresses.add(r[4][0])
            return list(addresses), f"AAAA records for {hostname}"
    except socket.gaierror as e:
        return [], f"Error: {e}"
    return [], "No results"

def resolve_dnspython(hostname, qtype=None):
    """Use dnspython for full DNS resolution."""
    try:
        import dns.resolver
        import dns.rdatatype
    except ImportError:
        return None
    results = []
    types = [qtype] if qtype and qtype != "all" else ["A", "AAAA", "MX", "TXT", "NS", "CNAME", "SOA"]
    for t in types:
        try:
            answers = dns.resolver.resolve(hostname, t)
            for rdata in answers:
                results.append((t, str(rdata)))
        except Exception:
            pass
    return results if results else None

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: dns-lookup <domain> [--type A|AAAA|MX|TXT|NS|CNAME|SOA|all]", file=sys.stderr)
        print("  Default: A record", file=sys.stderr)
        sys.exit(1)
    hostname = args[0]
    qtype = "A"
    if "--type" in args:
        idx = args.index("--type")
        if idx + 1 < len(args):
            qtype = args[idx + 1].upper()
    if qtype not in RECORD_TYPES:
        print(f"Unknown record type: {qtype}", file=sys.stderr)
        print(f"Supported: {', '.join(RECORD_TYPES.keys())}", file=sys.stderr)
        sys.exit(1)
    # Try dnspython first
    dns_results = resolve_dnspython(hostname, qtype)
    if dns_results:
        for t, val in dns_results:
            print(f"{t:<6} {val}")
        return
    # Fallback to socket
    addresses, label = resolve_socket(hostname, qtype)
    if addresses:
        for addr in addresses:
            print(f"{qtype:<6} {addr}")
    else:
        print(label or f"No {qtype} records found for {hostname}")

if __name__ == "__main__":
    main()
