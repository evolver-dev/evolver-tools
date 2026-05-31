#!/usr/bin/env python3
"""rot13 — ROT13/ROT47 text cipher.

Usage: rot13 "Hello World"
       echo "Hello" | rot13 [--rot47]
       rot13 --rot47 "p6xx2F5H~"

Applies ROT13 (default) or ROT47 cipher.
Zero-dependency (stdlib only).
"""

import sys

ROT13_TRANS = str.maketrans(
    'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',
    'NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm'
)


def rot13(text):
    return text.translate(ROT13_TRANS)


def rot47(text):
    result = []
    for c in text:
        o = ord(c)
        if 33 <= o <= 126:
            result.append(chr(33 + ((o - 33 + 47) % 94)))
        else:
            result.append(c)
    return ''.join(result)


def main():
    args = sys.argv[1:]
    use_rot47 = False

    for a in args[:]:
        if a in ('--rot47', '-7'):
            use_rot47 = True
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
        print("Usage: rot13 <text> or echo <text> | rot13 [--rot47]")
        return

    if use_rot47:
        print(rot47(text))
    else:
        print(rot13(text))


# === Auto-registration metadata ===
TOOL_META = {
    "name": "rot13",
    "func": "main",
    "desc": 'ROT13/ROT47 text cipher (stdin or arg)',
}

if __name__ == '__main__':
    main()
