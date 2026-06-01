#!/usr/bin/env python3
"""hexdump — Hex dump with ASCII view.

Usage: hexdump <file>
       echo "hello" | hexdump [--length N]

Shows offset, hex bytes, and ASCII representation.
Zero-dependency (stdlib only).
"""

import sys
import os


def hexdump(data, length=16):
    result = []
    for i in range(0, len(data), length):
        chunk = data[i:i + length]
        hex_part = ' '.join(f'{b:02x}' for b in chunk)
        # Pad hex part if needed
        hex_part = hex_part.ljust(length * 3 - 1)
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        result.append(f'{i:08x}  {hex_part}  |{ascii_part}|')
    return '\n'.join(result)


def main():
    args = sys.argv[1:]
    show_len = 16

    for a in args[:]:
        if a == '--length' and len(args) > args.index(a) + 1:
            idx = args.index(a)
            show_len = int(args[idx + 1])
            args.remove(a)
            args.pop(idx)  # remove the value too... but index shifted
        elif a.startswith('--length='):
            show_len = int(a.split('=', 1)[1])
            args.remove(a)
        elif a in ('-h', '--help'):
            print(__doc__)
            return

    # Re-parse length properly
    args = sys.argv[1:]
    filtered = []
    i = 0
    while i < len(args):
        if args[i] == '--length' and i + 1 < len(args):
            show_len = int(args[i + 1])
            i += 2
        elif args[i].startswith('--length='):
            show_len = int(args[i].split('=', 1)[1])
            i += 1
        elif args[i] in ('-h', '--help'):
            print(__doc__)
            return
        else:
            filtered.append(args[i])
            i += 1

    if filtered:
        path = filtered[0]
        if not os.path.isfile(path):
            print(f"Error: file not found: {path}", file=sys.stderr)
            sys.exit(1)
        with open(path, 'rb') as f:
            data = f.read()
        print(hexdump(data, show_len))
    elif not sys.stdin.isatty():
        data = sys.stdin.buffer.read()
        print(hexdump(data, show_len))
    else:
        print("Usage: hexdump <file>")
        print("       cat <file> | hexdump")
        return


# === Auto-registration metadata ===
TOOL_META = {
    "name": "hexdump",
    "func": "main",
    "desc": 'Hex dump with ASCII view (file or stdin)',
}

if __name__ == '__main__':
    main()
