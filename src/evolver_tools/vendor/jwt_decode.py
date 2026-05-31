#!/usr/bin/env python3
"""jwt-decode — Decode JWT tokens (header + payload, no verification).

Usage: jwt-decode <token>
       echo <token> | jwt-decode

Zero-dependency (stdlib only — uses base64 + json).
"""
import sys
import base64
import json


def decode_part(data: str) -> str:
    # Add padding
    padding = 4 - len(data) % 4
    if padding != 4:
        data += '=' * padding
    try:
        decoded = base64.urlsafe_b64decode(data)
        return decoded.decode('utf-8')
    except Exception:
        return f'[binary data: {len(data)} bytes]'


def main():
    args = sys.argv[1:]

    if '-h' in args or '--help' in args:
        print(__doc__)
        return

    if args:
        token = args[0]
    else:
        token = sys.stdin.read().strip()

    if not token:
        print('Error: No JWT token provided', file=sys.stderr)
        sys.exit(1)

    parts = token.split('.')
    if len(parts) != 3:
        print('Error: Invalid JWT — expected 3 dot-separated parts', file=sys.stderr)
        sys.exit(1)

    print('=== JWT Decode (no verification) ===')
    print()

    # Header
    header_raw = decode_part(parts[0])
    try:
        header = json.loads(header_raw)
        print(f'Header: {json.dumps(header, indent=2)}')
    except json.JSONDecodeError:
        print(f'Header (raw): {header_raw}')

    print()

    # Payload
    payload_raw = decode_part(parts[1])
    try:
        payload = json.loads(payload_raw)
        print(f'Payload: {json.dumps(payload, indent=2)}')
    except json.JSONDecodeError:
        print(f'Payload (raw): {payload_raw}')

    print()
    print(f'Signature: {parts[2][:40]}... ({len(parts[2])} chars)')
    print()
    print('WARNING: Decoded only — signature NOT verified.')


TOOL_META = {
    "name": "jwt-decode",
    "func": "main",
    "desc": "Decode JWT tokens (header + payload, no verification)",
}

if __name__ == '__main__':
    main()
