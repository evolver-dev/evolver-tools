#!/usr/bin/env python3
"""otp-gen — One-time password generator (TOTP/HOTP).

Usage: otp-gen --secret=<base32_secret>
       otp-gen --generate  (generate a new secret)
       otp-gen --secret=<secret> --counter=42  (HOTP variant)

Generates time-based one-time passwords (TOTP) compatible with
Google Authenticator, Authy, etc.
Zero-dependency (stdlib only).
"""

import sys, time, struct, hashlib, hmac, base64

def hotp(secret: bytes, counter: int, digits=6) -> str:
    """Generate HMAC-based one-time password."""
    msg = struct.pack('>Q', counter)
    h = hmac.new(secret, msg, hashlib.sha1).digest()
    offset = h[-1] & 0x0f
    code = (struct.unpack('>I', h[offset:offset+4])[0] & 0x7fffffff) % (10**digits)
    return str(code).zfill(digits)

def totp(secret: bytes, time_step=30, digits=6) -> str:
    """Generate time-based one-time password."""
    counter = int(time.time() / time_step)
    return hotp(secret, counter, digits)

def b32_decode(s: str) -> bytes:
    """Base32 decode with padding."""
    s = s.upper().replace(' ', '')
    padding = (8 - len(s) % 8) % 8
    s += '=' * padding
    return base64.b32decode(s)

def generate_secret() -> bytes:
    """Generate a random 20-byte secret."""
    return hashlib.sha256(str(time.time()).encode() + str(hashlib.sha256).encode()).digest()[:20]

def main():
    args = sys.argv[1:]
    secret = None
    counter = None
    digits = 6
    gen = False

    for a in args:
        if a.startswith('--secret='):
            secret = a.split('=', 1)[1]
        elif a.startswith('--counter='):
            counter = int(a.split('=', 1)[1])
        elif a.startswith('--digits='):
            digits = int(a.split('=', 1)[1])
        elif a == '--generate':
            gen = True
        elif a in ('-h', '--help'):
            print(__doc__)
            return

    if gen:
        secret_bytes = generate_secret()
        secret_b32 = base64.b32encode(secret_bytes).decode().rstrip('=')
        print(f"  New secret (base32): {secret_b32}")
        print(f"  Add to authenticator app")
        # Show current OTP
        print(f"  Current OTP: {hotp(secret_bytes, int(time.time()/30), digits)}")
        return

    if not secret:
        print("Usage: otp-gen --secret=<base32_secret> [--digits=6]")
        print("       otp-gen --generate")
        return

    secret_bytes = b32_decode(secret)

    if counter is not None:
        code = hotp(secret_bytes, counter, digits)
        print(f"  HOTP: {code}  (counter={counter})")
    else:
        code = totp(secret_bytes, 30, digits)
        remaining = 30 - (int(time.time()) % 30)
        print(f"  TOTP: {code}  (expires in {remaining}s)")


# === Auto-registration metadata ===
TOOL_META = {
    "name": "otp-gen",
    "func": "main",
    "desc": 'TOTP/HOTP one-time password generator',
}

if __name__ == '__main__':
    main()
