#!/usr/bin/env python3
"""ssl-check — Check SSL/TLS certificate details for a domain.

Usage: ssl-check example.com [--port=443]
       ssl-check example.com --show-chain

Connects to a server and displays TLS certificate info.
Zero-dependency (stdlib only).
"""

import sys, socket, ssl, datetime

def check_cert(hostname, port=443, show_chain=False):
    """Connect to host and get certificate info."""
    context = ssl.create_default_context()
    
    with socket.create_connection((hostname, port), timeout=10) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            cert = ssock.getpeercert()
            
            if not cert:
                print("  No certificate information available")
                return
            
            print(f"  {'='*50}")
            print(f"  SSL Certificate for: {hostname}:{port}")
            print(f"  {'='*50}")
            print()
            
            # Subject
            subject = dict(x[0] for x in cert.get('subject', []))
            print(f"  Subject:")
            for k, v in subject.items():
                print(f"    {k}: {v}")
            
            # Issuer
            issuer = dict(x[0] for x in cert.get('issuer', []))
            print(f"  Issuer:")
            for k, v in issuer.items():
                print(f"    {k}: {v}")
            
            # Validity
            not_before = cert.get('notBefore', '')
            not_after = cert.get('notAfter', '')
            print(f"\n  Validity:")
            print(f"    Not before: {not_before}")
            print(f"    Not after:  {not_after}")
            
            # Parse dates for human readable
            try:
                from datetime import datetime as dt
                nb = dt.strptime(not_before, '%b %d %H:%M:%S %Y %Z')
                na = dt.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
                now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
                remaining = (na - now).days
                print(f"    Expires in: {remaining} days")
                if remaining < 30:
                    print(f"    ⚠ WARNING: Certificate expires soon!")
                elif remaining < 0:
                    print(f"    ❌ EXPIRED: {abs(remaining)} days ago")
                else:
                    print(f"    ✓ Valid: {remaining} days remaining")
            except:
                pass
            
            # SAN
            san = cert.get('subjectAltName', [])
            if san:
                print(f"\n  Subject Alternative Names:")
                for name_type, name in san:
                    print(f"    {name_type}: {name}")
            
            # Version
            print(f"\n  Version: {cert.get('version', 'N/A')}")
            print(f"  Serial: {cert.get('serialNumber', 'N/A')}")
            
            # Cipher
            cipher = ssock.cipher()
            print(f"\n  Connection:")
            print(f"    Cipher: {cipher[0]}")
            print(f"    Protocol: {cipher[1]}")
            print(f"    Bits: {cipher[2]}")

def main():
    args = sys.argv[1:]
    if not args or '-h' in args or '--help' in args:
        print(__doc__)
        return

    hostname = None
    port = 443
    show_chain = False

    for a in args:
        if a.startswith('--port='):
            port = int(a.split('=', 1)[1])
        elif a == '--show-chain':
            show_chain = True
        elif not a.startswith('-') and '.' in a:
            hostname = a

    if not hostname:
        print("Error: hostname required (e.g., example.com)")
        sys.exit(1)

    try:
        check_cert(hostname, port, show_chain)
    except socket.timeout:
        print(f"  Connection timeout: {hostname}:{port}")
        sys.exit(1)
    except ssl.SSLError as e:
        print(f"  SSL error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"  Error: {e}")
        sys.exit(1)


# === Auto-registration metadata ===
TOOL_META = {
    "name": "ssl-check",
    "func": "main",
    "desc": 'SSL/TLS certificate checker',
}

if __name__ == '__main__':
    main()
