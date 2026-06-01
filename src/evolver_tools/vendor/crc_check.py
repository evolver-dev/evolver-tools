#!/usr/bin/env python3
"""crc_check — CRC32/CRC64 checksum calculator for files.

Usage: crc_check file.bin
       crc_check --crc64 file.bin
       crc_check --all file.bin
       cat file.bin | crc_check

Verify file integrity with CRC checksums.
Zero external dependencies (zlib.crc32 + pure Python CRC64).
"""

import sys
import os
import zlib

TOOL_META = {
    "name": "crc_check",
    "func": "main",
    "desc": "CRC32/CRC64 checksum calculator for files",
}

def crc64(data):
    """Compute CRC64-ECMA-182."""
    poly = 0xC96C5795D7870F42
    crc = 0xFFFFFFFFFFFFFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ poly
            else:
                crc >>= 1
    return crc ^ 0xFFFFFFFFFFFFFFFF


def main():
    args = sys.argv[1:]
    mode = 'crc32'
    files = []

    i = 0
    while i < len(args):
        if args[i] in ('-h', '--help'):
            print(__doc__)
            return
        elif args[i] == '--crc64':
            mode = 'crc64'
            i += 1
        elif args[i] == '--all':
            mode = 'all'
            i += 1
        elif args[i].startswith('--'):
            print(f"Unknown flag: {args[i]}", file=sys.stderr)
            sys.exit(1)
        else:
            files.append(args[i])
            i += 1

    if files:
        for path in files:
            if not os.path.exists(path):
                print(f"Error: file not found: {path}", file=sys.stderr)
                sys.exit(1)
            with open(path, 'rb') as f:
                data = f.read()
            name = os.path.basename(path)
            if mode in ('crc32', 'all'):
                print(f"CRC32({name}) = {zlib.crc32(data) & 0xFFFFFFFF:08x}")
            if mode in ('crc64', 'all'):
                print(f"CRC64({name}) = {crc64(data):016x}")
    else:
        data = sys.stdin.buffer.read()
        if mode in ('crc32', 'all'):
            print(f"CRC32 = {zlib.crc32(data) & 0xFFFFFFFF:08x}")
        if mode in ('crc64', 'all'):
            print(f"CRC64 = {crc64(data):016x}")
