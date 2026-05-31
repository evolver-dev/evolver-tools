#!/usr/bin/env python3
"""base32 — Base32 encoding/decoding tool.

Usage: base32 encode "hello"
       base32 decode "NBSWY3DP"
       echo "hello" | base32 encode

Zero-dependency (stdlib only).
"""

import sys
import base64


def main():
    args = sys.argv[1:]

    mode = 'encode'
    for a in args[:]:
        if a in ('encode', '--encode', '-e'):
            mode = 'encode'
            args.remove(a)
        elif a in ('decode', '--decode', '-d'):
            mode = 'decode'
            args.remove(a)
        elif a in ('-h', '--help'):
            print(__doc__)
            return

    text_args = [a for a in args if not a.startswith('-')]

    if text_args:
        text = ' '.join(text_args)
    elif not sys.stdin.isatty():
        text = sys.stdin.read().strip()
    else:
        print("Usage: base32 (encode|decode) [text]")
        print("       echo <text> | base32 encode")
        return

    if mode == 'encode':
        encoded = base64.b32encode(text.encode()).decode()
        print(encoded)
    else:
        try:
            decoded = base64.b32decode(text.upper().encode()).decode()
            print(decoded)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


# === Auto-registration metadata ===
TOOL_META = {
    "name": "base32",
    "func": "main",
    "desc": 'Base32 encode/decode (stdin or arg)',
}

if __name__ == '__main__':
    main()
