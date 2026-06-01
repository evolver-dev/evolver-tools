#!/usr/bin/env python3
"""file-splitter — Split large files into smaller chunks."""
import os
import sys

TOOL_META = {
    "name": "file-splitter",
    "func": "main",
    "desc": "Split files into chunks. Usage: file-splitter <file> --lines N | --size N[K|M|G]",
}

def format_size(size):
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TB"

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: file-splitter <file> --lines N")
        print("       file-splitter <file> --size N[K|M|G]")
        print("       file-splitter <file> --chunks N")
        return
    filepath = args[0]
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    split_lines = None
    split_size = None
    num_chunks = None
    i = 1
    while i < len(args):
        if args[i] == "--lines" and i + 1 < len(args):
            split_lines = int(args[i + 1])
            i += 2
        elif args[i] == "--size" and i + 1 < len(args):
            val = args[i + 1].upper()
            if val.endswith("K"):
                split_size = int(val[:-1]) * 1024
            elif val.endswith("M"):
                split_size = int(val[:-1]) * 1024 * 1024
            elif val.endswith("G"):
                split_size = int(val[:-1]) * 1024 * 1024 * 1024
            else:
                split_size = int(val)
            i += 2
        elif args[i] == "--chunks" and i + 1 < len(args):
            num_chunks = int(args[i + 1])
            i += 2
        else:
            i += 1
    total_size = os.path.getsize(filepath)
    total_lines = 0
    with open(filepath) as f:
        for _ in f:
            total_lines += 1
    if num_chunks:
        split_lines = max(1, total_lines // num_chunks)
    if split_lines:
        base, ext = os.path.splitext(filepath)
        chunk_num = 1
        with open(filepath) as f:
            out_lines = []
            out_size = 0
            for line in f:
                out_lines.append(line)
                out_size += len(line)
                if len(out_lines) >= split_lines:
                    chunk_file = f"{base}.part{chunk_num:03d}{ext}"
                    with open(chunk_file, "w") as cf:
                        cf.writelines(out_lines)
                    print(f"  Created: {chunk_file} ({format_size(out_size)})")
                    out_lines = []
                    out_size = 0
                    chunk_num += 1
            if out_lines:
                chunk_file = f"{base}.part{chunk_num:03d}{ext}"
                with open(chunk_file, "w") as cf:
                    cf.writelines(out_lines)
                print(f"  Created: {chunk_file} ({format_size(out_size)})")
        print(f"Split {filepath} into {chunk_num} parts ({format_size(total_size)} total)")
    elif split_size:
        base, ext = os.path.splitext(filepath)
        chunk_num = 1
        with open(filepath) as f:
            out_data = b""
            if ext.lower() in (".txt", ".py", ".md", ".json", ".csv", ".yaml", ".yml", ".xml", ".html", ".css", ".js"):
                # Text mode
                f_text = open(filepath, "r")
                out_lines = []
                out_bytes = 0
                for line in f_text:
                    out_lines.append(line)
                    out_bytes += len(line.encode())
                    if out_bytes >= split_size:
                        chunk_file = f"{base}.part{chunk_num:03d}{ext}"
                        with open(chunk_file, "w") as cf:
                            cf.writelines(out_lines)
                        print(f"  Created: {chunk_file} ({format_size(out_bytes)})")
                        out_lines = []
                        out_bytes = 0
                        chunk_num += 1
                if out_lines:
                    chunk_file = f"{base}.part{chunk_num:03d}{ext}"
                    with open(chunk_file, "w") as cf:
                        cf.writelines(out_lines)
                    print(f"  Created: {chunk_file} ({format_size(out_bytes)})")
                f_text.close()
            else:
                # Binary mode
                with open(filepath, "rb") as f:
                    while True:
                        chunk = f.read(split_size)
                        if not chunk:
                            break
                        chunk_file = f"{base}.part{chunk_num:03d}{ext}"
                        with open(chunk_file, "wb") as cf:
                            cf.write(chunk)
                        print(f"  Created: {chunk_file} ({format_size(len(chunk))})")
                        chunk_num += 1
            print(f"Split {filepath} into {chunk_num - 1} parts ({format_size(total_size)} total)")
    else:
        print("Specify --lines N, --size N, or --chunks N", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
