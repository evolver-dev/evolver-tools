#!/usr/bin/env python3
"""gzip-cli — Gzip/gunzip files from CLI.

Usage: gzip-cli <file>          # Compress (creates .gz)
       gzip-cli -d <file.gz>    # Decompress
       gzip-cli -l <file.gz>    # List contents of archive
       cat <file> | gzip-cli    # Compress stdin to stdout

Zero-dependency (stdlib only — uses gzip).
"""
import sys
import os
import gzip


def main():
    args = sys.argv[1:]

    if '-h' in args or '--help' in args:
        print(__doc__)
        return

    decompress = '-d' in args
    list_mode = '-l' in args
    args = [a for a in args if not a.startswith('-') or a in (args and args[0] and args[0])]

    # Actually re-parse properly
    args = sys.argv[1:]
    decompress = '-d' in args or '--decompress' in args
    list_mode = '-l' in args or '--list' in args
    args = [a for a in args if not a.startswith('-')]

    # Stdin mode
    if not args:
        if decompress:
            sys.stdout.buffer.write(gzip.decompress(sys.stdin.buffer.read()))
        else:
            sys.stdout.buffer.write(gzip.compress(sys.stdin.buffer.read()))
        return

    for filepath in args:
        if not os.path.exists(filepath):
            print(f'Error: File not found: {filepath}', file=sys.stderr)
            continue

        if list_mode:
            with gzip.open(filepath, 'rb') as f:
                content = f.read()
            orig_name = os.path.basename(filepath)
            if orig_name.endswith('.gz'):
                orig_name = orig_name[:-3]
            compressed_size = os.path.getsize(filepath)
            print(f'{orig_name:20s}  {len(content):>8} bytes  →  {compressed_size:>8} bytes  (ratio: {compressed_size/len(content)*100:.1f}%)')
            continue

        if decompress:
            if not filepath.endswith('.gz'):
                print(f'Warning: {filepath} does not end in .gz, decompressing anyway', file=sys.stderr)
            outpath = filepath[:-3] if filepath.endswith('.gz') else filepath + '.out'
            with gzip.open(filepath, 'rb') as f_in:
                content = f_in.read()
            with open(outpath, 'wb') as f_out:
                f_out.write(content)
            print(f'{filepath} → {outpath} ({len(content)} bytes)')
        else:
            outpath = filepath + '.gz'
            with open(filepath, 'rb') as f_in:
                content = f_in.read()
            with gzip.open(outpath, 'wb') as f_out:
                f_out.write(content)
            print(f'{filepath} → {outpath} ({os.path.getsize(outpath)} bytes, ratio: {os.path.getsize(outpath)/len(content)*100:.1f}%)')


TOOL_META = {
    "name": "gzip-cli",
    "func": "main",
    "desc": "Gzip/gunzip files — compress, decompress, list archive contents",
}

if __name__ == '__main__':
    main()
