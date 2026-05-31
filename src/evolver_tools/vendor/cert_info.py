#!/usr/bin/env python3
"""cert-info — Display SSL certificate details for a domain."""
import ssl
import socket
import sys
from datetime import datetime

TOOL_META = {
    "name": "cert-info",
    "func": "main",
    "desc": "Show SSL certificate info for a domain. Usage: cert-info <domain> [port]",
}

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: cert-info <domain> [port]", file=sys.stderr)
        print("  Default port: 443", file=sys.stderr)
        sys.exit(1)
    host = args[0]
    port = int(args[1]) if len(args) > 1 else 443
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
        if not cert:
            print(f"No certificate returned by {host}:{port}", file=sys.stderr)
            sys.exit(1)
        print(f"SSL Certificate for {host}:{port}")
        print("=" * 50)
        # Subject
        subject = dict(x[0] for x in cert.get("subject", []))
        print(f"Subject:")
        for key, val in subject.items():
            print(f"  {key}: {val}")
        # Issuer
        issuer = dict(x[0] for x in cert.get("issuer", []))
        print(f"Issuer:")
        for key, val in issuer.items():
            print(f"  {key}: {val}")
        # Validity
        print(f"Valid from:  {cert.get('notBefore', 'N/A')}")
        print(f"Valid until: {cert.get('notAfter', 'N/A')}")
        # Check expiry
        try:
            not_after = cert.get("notAfter", "")
            expiry = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
            now = datetime.utcnow()
            remaining = (expiry - now).days
            if remaining < 0:
                print(f"⚠ EXPIRED {abs(remaining)} days ago!")
            elif remaining < 30:
                print(f"⚠ Expires in {remaining} days (soon!)")
            else:
                print(f"✓ Expires in {remaining} days")
        except Exception:
            pass
        # SAN
        san = cert.get("subjectAltName", [])
        if san:
            print(f"Subject Alt Names ({len(san)}):")
            for _, name in san[:10]:
                print(f"  {name}")
            if len(san) > 10:
                print(f"  ... and {len(san) - 10} more")
        # Serial
        serial = cert.get("serialNumber", "")
        if serial:
            print(f"Serial:      {serial}")
        # Version
        print(f"Version:     {cert.get('version', 'N/A')}")
        # Fingerprints
        try:
            der = ssock.getpeercert(binary_form=True)
            import hashlib
            print(f"SHA256:      {hashlib.sha256(der).hexdigest()}")
            print(f"SHA1:        {hashlib.sha1(der).hexdigest()}")
        except Exception:
            pass
    except ssl.SSLError as e:
        print(f"SSL Error: {e}", file=sys.stderr)
        sys.exit(1)
    except socket.gaierror:
        print(f"Could not resolve: {host}", file=sys.stderr)
        sys.exit(1)
    except socket.timeout:
        print(f"Connection timed out: {host}:{port}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
