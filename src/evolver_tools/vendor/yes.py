#!/usr/bin/env python3
"""yes — Output a string repeatedly until killed.

Usage: yes
       yes "hello world"
       yes | command

Like standard Unix 'yes' command.
Zero-dependency (stdlib only).
"""

import sys


def main():
    args = sys.argv[1:]

    if '-h' in args or '--help' in args:
        print(__doc__)
        return

    text = ' '.join(args) if args else 'y'

    try:
        while True:
            print(text)
    except (KeyboardInterrupt, BrokenPipeError):
        pass


# === Auto-registration metadata ===
TOOL_META = {
    "name": "yes",
    "func": "main",
    "desc": 'Output a string repeatedly until killed',
}

if __name__ == '__main__':
    main()
