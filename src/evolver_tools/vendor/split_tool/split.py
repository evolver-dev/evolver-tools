#!/usr/bin/env python3
"""split — File split and join utility

Split large files into smaller chunks, or join chunks back.

Usage:
    split -l 1000 bigfile.txt        # Split into 1000-line chunks
    split -b 10M bigfile.txt         # Split into 10MB chunks
    split -l 500 -p chunk_ big.txt   # Custom prefix
    split --join chunk_prefix out.txt # Join chunks back
    cat bigfile.txt | split -l 100   # Stdin split
"""
import sys
import os
import math


def format_size(size):
    """Format byte size to human-readable."""
    for unit in ('B', 'K', 'M', 'G', 'T'):
        if size < 1024:
            return f"{size:.1f}{unit}" if isinstance(size, float) else f"{size}{unit}"
        size /= 1024
    return f"{size:.1f}P"


def parse_size(text):
    """Parse human-readable size (10M, 1G, 500K) to bytes."""
    text = text.strip().upper()
    multipliers = {'K': 1024, 'M': 1024**2, 'G': 1024**3, 'T': 1024**4}
    if text[-1] in multipliers:
        return int(float(text[:-1]) * multipliers[text[-1]])
    return int(text)


def split_by_lines(lines, chunk_lines, prefix, out_dir):
    """Split lines into files by line count."""
    total = len(lines)
    num_chunks = math.ceil(total / chunk_lines)
    pad = len(str(num_chunks))
    files_created = []

    for i in range(0, total, chunk_lines):
        chunk = lines[i:i + chunk_lines]
        chunk_num = (i // chunk_lines) + 1
        filename = f"{prefix}{chunk_num:0{pad}d}.txt"
        filepath = os.path.join(out_dir, filename) if out_dir else filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(line + '\n' if not line.endswith('\n') else line for line in chunk)
        files_created.append(filepath)
        print(f"  Created: {filepath} ({len(chunk)} lines)")
    return files_created


def split_by_size(lines, chunk_size, prefix, out_dir):
    """Split into files by byte size."""
    chunk_num = 1
    current_size = 0
    current_chunk = []
    files_created = []
    pad = 3

    for line in lines:
        line_bytes = len(line.encode('utf-8')) + 1  # +1 for newline
        if current_size + line_bytes > chunk_size and current_chunk:
            filename = f"{prefix}{chunk_num:0{pad}d}.txt"
            filepath = os.path.join(out_dir, filename) if out_dir else filename
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(line + '\n' if not line.endswith('\n') else line for line in current_chunk)
            files_created.append(filepath)
            print(f"  Created: {filepath} ({format_size(current_size)})")
            current_chunk = []
            current_size = 0
            chunk_num += 1
        current_chunk.append(line)
        current_size += line_bytes

    if current_chunk:
        filename = f"{prefix}{chunk_num:0{pad}d}.txt"
        filepath = os.path.join(out_dir, filename) if out_dir else filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(line + '\n' if not line.endswith('\n') else line for line in current_chunk)
        files_created.append(filepath)
        print(f"  Created: {filepath} ({format_size(current_size)})")

    return files_created


def join_chunks(prefix, output_file):
    """Join chunk files into single file."""
    if os.path.isdir(prefix):
        # List chunk files in directory
        files = sorted(os.listdir(prefix))
        base_dir = prefix
    else:
        base_dir = os.path.dirname(prefix) or '.'
        pattern = os.path.basename(prefix)
        files = sorted(f for f in os.listdir(base_dir) if f.startswith(pattern))

    if not files:
        print(f"Error: no chunk files found matching '{prefix}'", file=sys.stderr)
        sys.exit(1)

    file_count = 0
    with open(output_file, 'w', encoding='utf-8') as out:
        for fname in files:
            fpath = os.path.join(base_dir, fname)
            if os.path.isfile(fpath):
                with open(fpath, 'r', encoding='utf-8') as f:
                    out.write(f.read())
                    if not f.read().endswith('\n'):
                        out.write('\n')
                file_count += 1
    print(f"Joined {file_count} files into {output_file}")


def main():
    args = sys.argv[1:]

    if not args or args[0] in ('-h', '--help'):
        print(__doc__.strip())
        return

    join_mode = False
    lines_per_file = None
    bytes_per_file = None
    prefix = 'x'
    out_dir = '.'

    i = 0
    files = []
    while i < len(args):
        arg = args[i]
        if arg == '--join':
            join_mode = True
        elif arg == '-l':
            i += 1
            if i < len(args):
                lines_per_file = int(args[i])
        elif arg == '-b':
            i += 1
            if i < len(args):
                bytes_per_file = parse_size(args[i])
        elif arg == '-p':
            i += 1
            if i < len(args):
                prefix = args[i]
        elif arg == '-o':
            i += 1
            if i < len(args):
                out_dir = args[i]
        elif arg.startswith('-'):
            print(f"Error: unknown option '{arg}'", file=sys.stderr)
            sys.exit(1)
        else:
            files.append(arg)
        i += 1

    if join_mode:
        if not files or len(files) < 2:
            print("Error: --join requires <prefix/dir> <output>", file=sys.stderr)
            sys.exit(1)
        join_chunks(files[0], files[1])
        return

    if not files:
        # Stdin mode
        text = sys.stdin.readlines()
    else:
        filepath = files[0]
        if not os.path.isfile(filepath):
            print(f"Error: file not found: {filepath}", file=sys.stderr)
            sys.exit(1)
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.readlines()

    total_lines = len(text)
    print(f"Total: {total_lines} lines")

    if lines_per_file:
        split_by_lines(text, lines_per_file, prefix, out_dir)
    elif bytes_per_file:
        split_by_size(text, bytes_per_file, prefix, out_dir)
    else:
        # Default: 1000 lines per file
        split_by_lines(text, 1000, prefix, out_dir)


if __name__ == '__main__':
    main()
