#!/usr/bin/env python3
"""otp-gen — TOTP/HOTP one-time password generator. Generate TOTP codes from a base32 secret."""

import sys
import os
import time
import struct
import hashlib
import hmac
import base64
import json
import argparse


CONFIG_DIR = os.path.expanduser('~/.config/evolver-otp')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'secrets.json')


def load_secrets():
    """Load OTP secrets from config file."""
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_secrets(secrets):
    """Save OTP secrets to config file."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(secrets, f, indent=2)


def hotp(secret_bytes, counter, digits=6):
    """Generate an HOTP code."""
    counter_bytes = struct.pack('>Q', counter)
    h = hmac.new(secret_bytes, counter_bytes, hashlib.sha1).digest()
    offset = h[-1] & 0x0f
    truncated = struct.unpack('>I', h[offset:offset+4])[0] & 0x7fffffff
    code = truncated % (10 ** digits)
    return str(code).zfill(digits)


def totp(secret_bytes, digits=6, period=30):
    """Generate a TOTP code for the current time."""
    counter = int(time.time()) // period
    return hotp(secret_bytes, counter, digits)


def base32_decode(secret_str):
    """Decode a base32 secret, padding if needed."""
    padding = 8 - (len(secret_str) % 8)
    if padding != 8:
        secret_str += '=' * padding
    try:
        return base64.b32decode(secret_str.upper())
    except Exception as e:
        print(f"Invalid base32 secret: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_add(args):
    """Add a new OTP service."""
    secrets = load_secrets()
    secrets[args.name] = {
        'secret': args.secret,
        'digits': args.digits or 6,
        'period': args.period or 30,
        'algorithm': 'SHA1',
    }
    save_secrets(secrets)
    print(f"Added OTP service: \033[1m{args.name}\033[0m")


def cmd_list(args):
    """List all configured OTP services."""
    secrets = load_secrets()
    if not secrets:
        print("No OTP services configured.")
        return

    print(f"\033[1mConfigured OTP Services:\033[0m")
    for name in sorted(secrets.keys()):
        info = secrets[name]
        secret_preview = info['secret'][:6] + '...' + info['secret'][-4:] if len(info['secret']) > 12 else info['secret']
        print(f"  \033[33m{name}\033[0m ({info.get('digits', 6)} digits, {info.get('period', 30)}s period)  \033[90m[{secret_preview}]\033[0m")


def cmd_show(args):
    """Show current TOTP code for a service."""
    secrets = load_secrets()
    if args.name not in secrets:
        print(f"Service '{args.name}' not found.", file=sys.stderr)
        available = ', '.join(sorted(secrets.keys()))
        if available:
            print(f"Available: {available}", file=sys.stderr)
        sys.exit(1)

    info = secrets[args.name]
    secret_bytes = base32_decode(info['secret'])
    digits = info.get('digits', 6)
    period = info.get('period', 30)

    code = totp(secret_bytes, digits, period)
    remaining = period - (int(time.time()) % period)

    bar_len = 10
    filled = int((period - remaining) / period * bar_len)
    bar = '█' * filled + '░' * (bar_len - filled)

    print(f"\033[1m{args.name}\033[0m")
    print(f"  Code: \033[1;92m{code}\033[0m")
    print(f"  Remaining: \033[94m{remaining}s\033[0m {bar} [{period}s period]")


def cmd_qrcode(args):
    """Generate a QR code URI for an OTP service (no actual QR image, shows URI)."""
    secrets = load_secrets()
    if args.name not in secrets:
        print(f"Service '{args.name}' not found.", file=sys.stderr)
        sys.exit(1)

    info = secrets[args.name]
    import urllib.parse
    label = urllib.parse.quote(args.name)
    secret = info['secret']
    issuer = urllib.parse.quote(args.issuer or args.name)
    digits = info.get('digits', 6)
    period = info.get('period', 30)

    uri = f"otpauth://totp/{label}?secret={secret}&issuer={issuer}&algorithm=SHA1&digits={digits}&period={period}"
    print(f"\033[1mOTP URI for {args.name}:\033[0m")
    print(f"  \033[94m{uri}\033[0m")
    print()
    print(f"\033[90mPaste this URI into your authenticator app, or use a QR generator.\033[0m")

    # Simple ASCII QR representation using blocks
    if not args.no_ascii:
        print()
        print("\033[90m(ASCII QR placeholder — use a QR code generator for scanning)\033[0m")


def cmd_remove(args):
    """Remove an OTP service."""
    secrets = load_secrets()
    if args.name not in secrets:
        print(f"Service '{args.name}' not found.", file=sys.stderr)
        sys.exit(1)
    del secrets[args.name]
    save_secrets(secrets)
    print(f"Removed OTP service: {args.name}")


def cmd_generate(args):
    """Generate a TOTP code directly from a secret."""
    secret_bytes = base32_decode(args.secret)
    code = totp(secret_bytes, args.digits or 6, args.period or 30)
    remaining = args.period or 30 - (int(time.time()) % (args.period or 30))
    print(f"Code: \033[1;92m{code}\033[0m  (\033[94m{remaining}s\033[0m remaining)")


def main():
    parser = argparse.ArgumentParser(
        description='TOTP/HOTP one-time password generator.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  otp-gen add "MyService" JBSWY3DPEHPK3PXP
  otp-gen list
  otp-gen show MyService
  otp-gen generate JBSWY3DPEHPK3PXP
  otp-gen qrcode MyService
        """,
    )
    sub = parser.add_subparsers(dest='command', help='Subcommand')

    p_add = sub.add_parser('add', help='Add a new OTP service')
    p_add.add_argument('name', help='Service name')
    p_add.add_argument('secret', help='Base32 secret key')
    p_add.add_argument('--digits', type=int, choices=[6, 8], default=6, help='Code digits (default: 6)')
    p_add.add_argument('--period', type=int, default=30, help='TOTP period in seconds (default: 30)')

    p_list = sub.add_parser('list', help='List configured services')

    p_show = sub.add_parser('show', help='Show current TOTP code')
    p_show.add_argument('name', help='Service name')

    p_rm = sub.add_parser('remove', help='Remove a service')
    p_rm.add_argument('name', help='Service name')

    p_qr = sub.add_parser('qrcode', help='Show OTP URI for QR code')
    p_qr.add_argument('name', help='Service name')
    p_qr.add_argument('--issuer', '-i', help='Issuer name (default: service name)')
    p_qr.add_argument('--no-ascii', action='store_true', help='Skip ASCII QR placeholder')

    p_gen = sub.add_parser('generate', help='Generate code from secret directly')
    p_gen.add_argument('secret', help='Base32 secret key')
    p_gen.add_argument('--digits', type=int, choices=[6, 8], default=6, help='Code digits')
    p_gen.add_argument('--period', type=int, default=30, help='TOTP period')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        cmds = {
            'add': cmd_add,
            'list': cmd_list,
            'show': cmd_show,
            'remove': cmd_remove,
            'qrcode': cmd_qrcode,
            'generate': cmd_generate,
        }
        cmds[args.command](args)
    except KeyboardInterrupt:
        print("\nAborted.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
