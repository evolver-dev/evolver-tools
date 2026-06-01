#!/usr/bin/env python3
"""random-string — Generate random strings with various charsets.

Usage: random-string [length] [--type <type>]
       random-string 16
       random-string 32 --type hex
       random-string 8 --type pin
       random-string 64 --type alphanumeric

Types: alphanumeric (default), alpha, numeric, hex, pin, base64, uuid
"""

import sys
import random
import string
import uuid


_CHARSETS = {
    'alpha': string.ascii_letters,
    'numeric': string.digits,
    'alphanumeric': string.ascii_letters + string.digits,
    'hex': string.hexdigits.lower(),
    'pin': string.digits,
    'base64': string.ascii_letters + string.digits + '+/',
}


def main():
    args = sys.argv[1:]
    if '-h' in args or '--help' in args:
        print(__doc__)
        return

    length = 16
    charset_type = 'alphanumeric'
    count = 1

    for i, a in enumerate(args):
        if a == '--type' and i + 1 < len(args):
            charset_type = args[i + 1]
        elif a == '--count' and i + 1 < len(args):
            count = int(args[i + 1])
        elif a.isdigit():
            length = int(a)

    if charset_type == 'uuid':
        for _ in range(count):
            print(str(uuid.uuid4()))
        return

    charset = _CHARSETS.get(charset_type, _CHARSETS['alphanumeric'])
    for _ in range(count):
        result = ''.join(random.choice(charset) for _ in range(length))
        print(result)


TOOL_META = {
    "name": "random-string",
    "func": "main",
    "desc": "Generate random strings (hex/pin/uuid/base64/alphanumeric)"
}
