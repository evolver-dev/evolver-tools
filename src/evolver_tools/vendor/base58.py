#!/usr/bin/env python3
"""base58 — Base58 encode/decode (Bitcoin-style alphabet).

Usage: base58 encode hello
       base58 decode 3yZe7d
       echo hello | base58 encode

Base58 uses Bitcoin alphabet (123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz).
No '0', 'O', 'I', 'l' — safe for human transcription.
"""

import sys

TOOL_META = {
    "name": "base58",
    "func": "main",
    "desc": "Base58 encode/decode (Bitcoin-style alphabet)",
}

ALPHABET = b'123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
BASE = 58

def b58encode(data):
    if isinstance(data, str):
        data = data.encode()
    n = int.from_bytes(data, 'big')
    if n == 0:
        return '1'
    res = []
    while n > 0:
        n, r = divmod(n, BASE)
        res.append(chr(ALPHABET[r]))
    # Leading zeros
    leading = 0
    for b in data:
        if b == 0:
            leading += 1
        else:
            break
    return '1' * leading + ''.join(reversed(res))


def b58decode(s):
    n = 0
    for c in s:
        idx = ALPHABET.find(c.encode() if isinstance(c, str) else c)
        if idx == -1:
            raise ValueError(f"Invalid Base58 character: {c}")
        n = n * BASE + idx
    # Count leading '1's
    leading = 0
    for c in s:
        if c == '1':
            leading += 1
        else:
            break
    result = n.to_bytes((n.bit_length() + 7) // 8, 'big') if n > 0 else b''
    return b'\x00' * leading + result


def main():
    args = sys.argv[1:]
    if not args or args[0] in ('-h', '--help'):
        print(__doc__)
        return

    mode = args[0]
    if mode not in ('encode', 'decode'):
        print("Usage: base58 encode|decode [text]", file=sys.stderr)
        sys.exit(1)

    if len(args) > 1:
        data = ' '.join(args[1:])
    else:
        data = sys.stdin.read().strip()

    if not data:
        print("Error: no input", file=sys.stderr)
        sys.exit(1)

    try:
        if mode == 'encode':
            result = b58encode(data.encode() if isinstance(data, str) else data)
        else:
            result = b58decode(data)
            try:
                result = result.decode('utf-8')
            except UnicodeDecodeError:
                result = result.hex()
        print(result)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
