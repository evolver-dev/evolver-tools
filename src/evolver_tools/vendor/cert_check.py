#!/usr/bin/env python3
"""cert-check — Check SSL certificate expiry. Fetch cert from host:port or local file."""
import sys
import os
import argparse
import json
import ssl
import socket
import datetime
from datetime import datetime as dt


def get_cert_from_host(host, port, timeout=10):
    """Fetch SSL certificate from a host:port."""
    try:
        context = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
                return cert
    except socket.gaierror as e:
        print(f"Error: Could not resolve hostname '{host}': {e}", file=sys.stderr)
        sys.exit(1)
    except socket.timeout:
        print(f"Error: Connection to {host}:{port} timed out", file=sys.stderr)
        sys.exit(1)
    except ConnectionRefusedError:
        print(f"Error: Connection refused to {host}:{port}", file=sys.stderr)
        sys.exit(1)
    except ssl.SSLError as e:
        print(f"Error: SSL error for {host}:{port}: {e}", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"Error: Could not connect to {host}:{port}: {e}", file=sys.stderr)
        sys.exit(1)


def get_cert_from_file(filepath):
    """Load certificate from a PEM file."""
    if not os.path.isfile(filepath):
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    try:
        context = ssl.create_default_context()
        # Load the cert to verify it
        with open(filepath, "rb") as f:
            cert_data = f.read()
        # Use OpenSSL to decode
        from cryptography import x509
        from cryptography.hazmat.backends import default_backend
        cert = x509.load_pem_x509_certificate(cert_data, default_backend())
        return parse_cryptography_cert(cert)
    except ImportError:
        print("Error: Reading PEM files requires 'cryptography' package. Use host:port mode instead.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading certificate from {filepath}: {e}", file=sys.stderr)
        sys.exit(1)


def parse_cryptography_cert(cert):
    """Parse a cryptography x509 certificate to dict."""
    info = {}
    try:
        info["subject"] = dict(cert.subject.rfc4514_string() for _ in [0])
        # Get subject as list of tuples
        subject_parts = []
        for attr in cert.subject:
            subject_parts.append(f"{attr.oid._name}={attr.value}")
        info["subject_str"] = ", ".join(subject_parts)
    except Exception:
        info["subject_str"] = str(cert.subject)

    try:
        issuer_parts = []
        for attr in cert.issuer:
            issuer_parts.append(f"{attr.oid._name}={attr.value}")
        info["issuer_str"] = ", ".join(issuer_parts)
    except Exception:
        info["issuer_str"] = str(cert.issuer)

    info["not_valid_before"] = cert.not_valid_before_utc.isoformat() if hasattr(cert, 'not_valid_before_utc') else str(cert.not_valid_before)
    info["not_valid_after"] = cert.not_valid_after_utc.isoformat() if hasattr(cert, 'not_valid_after_utc') else str(cert.not_valid_after)

    try:
        info["serial"] = hex(cert.serial_number)
    except Exception:
        info["serial"] = ""

    try:
        info["version"] = cert.version.value
    except Exception:
        info["version"] = ""

    try:
        san_ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
        info["san"] = [str(name) for name in san_ext.value]
    except Exception:
        info["san"] = []

    return info


def format_cert_info(cert, host, port, json_output=False):
    """Format certificate information for display."""
    # Parse dates
    not_before_str = cert.get("notBefore", "")
    not_after_str = cert.get("notAfter", "")

    try:
        not_before = dt.strptime(not_before_str, "%b %d %H:%M:%S %Y %Z")
    except (ValueError, TypeError):
        try:
            not_before = dt.strptime(not_before_str, "%Y%m%d%H%M%SZ")
        except (ValueError, TypeError):
            not_before = None

    try:
        not_after = dt.strptime(not_after_str, "%b %d %H:%M:%S %Y %Z")
    except (ValueError, TypeError):
        try:
            not_after = dt.strptime(not_after_str, "%Y%m%d%H%M%SZ")
        except (ValueError, TypeError):
            not_after = None

    # Calculate days remaining
    days_remaining = None
    if not_after:
        now = dt.now()
        if not_after.tzinfo:
            import time
            # Handle timezone-aware
            from datetime import timezone
            now_aware = dt.now(timezone.utc)
            delta = not_after - now_aware
        else:
            delta = not_after - now
        days_remaining = delta.days

    # Subject info
    subject = cert.get("subject", ())
    subject_parts = []
    for sub in subject:
        if isinstance(sub, tuple) and len(sub) >= 1:
            parts = []
            for item in sub:
                if isinstance(item, tuple) and len(item) == 2:
                    parts.append(f"{item[0]}={item[1]}")
            subject_parts.append(", ".join(parts))
    subject_str = "; ".join(subject_parts) if subject_parts else "N/A"

    # Issuer info
    issuer = cert.get("issuer", ())
    issuer_parts = []
    for iss in issuer:
        if isinstance(iss, tuple) and len(iss) >= 1:
            parts = []
            for item in iss:
                if isinstance(item, tuple) and len(item) == 2:
                    parts.append(f"{item[0]}={item[1]}")
            issuer_parts.append(", ".join(parts))
    issuer_str = "; ".join(issuer_parts) if issuer_parts else "N/A"

    # SAN
    san_list = []
    for sub in cert.get("subjectAltName", ()):
        if isinstance(sub, tuple) and len(sub) == 2:
            san_list.append(f"{sub[0]}:{sub[1]}")
    san_str = ", ".join(san_list) if san_list else "N/A"

    if json_output:
        output = {
            "host": host,
            "port": port,
            "subject": subject_str,
            "issuer": issuer_str,
            "serial": hex(cert.get("serialNumber", 0)) if isinstance(cert.get("serialNumber"), (int,)) else str(cert.get("serialNumber", "")),
            "version": cert.get("version", ""),
            "not_before": not_before_str,
            "not_after": not_after_str,
            "days_remaining": days_remaining,
            "san": san_list,
            "algorithm": cert.get("signatureAlgorithm", ""),
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"SSL Certificate for {host}:{port}")
        print(f"{'=' * 60}")
        print(f"  Subject:     {subject_str}")
        print(f"  Issuer:      {issuer_str}")
        print(f"  Serial:      {cert.get('serialNumber', 'N/A')}")
        print(f"  Version:     {cert.get('version', 'N/A')}")
        print(f"  Algorithm:   {cert.get('signatureAlgorithm', 'N/A')}")
        print()

        if not_before:
            print(f"  Valid From:  {not_before.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"  Valid From:  {not_before_str}")

        if not_after:
            print(f"  Valid Until: {not_after.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"  Valid Until: {not_after_str}")

        if days_remaining is not None:
            if days_remaining < 0:
                print(f"  Status:      \033[31mEXPIRED {abs(days_remaining)} days ago\033[0m")
            elif days_remaining < 30:
                print(f"  Status:      \033[33mEXPIRING SOON ({days_remaining} days remaining)\033[0m")
            elif days_remaining < 90:
                print(f"  Status:      \033[33m{days_remaining} days remaining\033[0m")
            else:
                print(f"  Status:      \033[32m{days_remaining} days remaining\033[0m")
        else:
            print(f"  Status:      Unknown")

        print()
        print(f"  Subject Alt Names: {san_str}")
        print(f"{'=' * 60}")


def main():
    parser = argparse.ArgumentParser(
        description="Check SSL certificate expiry. Fetch cert from host:port or local file."
    )
    parser.add_argument("target", nargs="?", help="Hostname or path to PEM file")
    parser.add_argument("port", nargs="?", type=int, default=443, help="Port (default: 443)")
    parser.add_argument("--file", "-f", action="store_true", help="Treat target as a PEM file path")
    parser.add_argument("--json", "-j", action="store_true", help="Output in JSON format")
    parser.add_argument("--timeout", type=int, default=10, help="Connection timeout in seconds")

    args = parser.parse_args()

    if not args.target:
        print("Error: Please provide a hostname or use --file for PEM files", file=sys.stderr)
        sys.exit(1)

    try:
        if args.file:
            # Load from PEM file
            cert_info = get_cert_from_file(args.target)
            format_cert_info(cert_info, args.target, 0, args.json)
        else:
            host = args.target
            port = args.port if args.port else 443
            cert = get_cert_from_host(host, port, args.timeout)
            format_cert_info(cert, host, port, args.json)
    except KeyboardInterrupt:
        print("\nInterrupted.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)



# === Auto-registration metadata ===
TOOL_META = {
    "name": "cert-check",
    "func": "main",
    "desc": 'Check SSL certificate expiry',
}

if __name__ == "__main__":
    main()
