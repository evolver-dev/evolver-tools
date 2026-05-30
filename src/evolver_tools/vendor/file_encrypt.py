#!/usr/bin/env python3
"""file-encrypt — Simple file encryption/decryption using XOR + base64.

Usage: file-encrypt --key=<passphrase> <file>
       cat secret.txt | file-encrypt --key=mypass [--decrypt]

Simple symmetric encryption for text files.
WARNING: Basic XOR cipher — not for high-security use.
Zero-dependency (stdlib only).
"""

import sys, os, base64, hashlib

def derive_key(passphrase: str) -> bytes:
    """Derive a 32-byte key from passphrase."""
    return hashlib.sha256(passphrase.encode()).digest()

def encrypt(data: bytes, key: bytes) -> bytes:
    """XOR encrypt with key cycling."""
    result = bytearray()
    for i, b in enumerate(data):
        result.append(b ^ key[i % len(key)])
    return bytes(result)

def main():
    args = sys.argv[1:]
    key = None
    decrypt = False
    files = []

    for a in args:
        if a.startswith('--key='):
            key = a.split('=', 1)[1]
        elif a == '--decrypt' or a == '-d':
            decrypt = True
        elif a in ('-h', '--help'):
            print(__doc__)
            return
        elif not a.startswith('-'):
            files.append(a)

    if not key:
        print("Error: --key=<passphrase> required", file=sys.stderr)
        sys.exit(1)

    key_bytes = derive_key(key)

    if files:
        for f in files:
            with open(f, 'rb') as fh:
                data = fh.read()
            if decrypt:
                encrypted = base64.b64decode(data.strip())
                result = encrypt(encrypted, key_bytes)
                out_path = f.replace('.enc', '.dec') if f.endswith('.enc') else f + '.dec'
            else:
                encrypted = encrypt(data, key_bytes)
                result = base64.b64encode(encrypted)
                out_path = f + '.enc'
            with open(out_path, 'wb') as fh:
                fh.write(result)
            print(f"  {'Decrypted' if decrypt else 'Encrypted'}: {f} → {out_path}")
    else:
        data = sys.stdin.buffer.read()
        if decrypt:
            encrypted = base64.b64decode(data.strip())
            result = encrypt(encrypted, key_bytes)
            sys.stdout.buffer.write(result)
        else:
            encrypted = encrypt(data, key_bytes)
            result = base64.b64encode(encrypted)
            sys.stdout.buffer.write(result)

if __name__ == '__main__':
    main()
