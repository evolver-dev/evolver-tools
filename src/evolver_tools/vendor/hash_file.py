#!/usr/bin/env python3
"""hash-file — Compute file hashes (MD5, SHA1, SHA256, SHA512)."""
import hashlib
import os
import sys

TOOL_META = {
    "name": "hash-file",
    "func": "main",
    "desc": "Compute file hashes. Usage: hash-file <file> [--md5|--sha1|--sha256|--sha512|--all]",
}

HASH_ALGOS = {
    "md5": hashlib.md5,
    "sha1": hashlib.sha1,
    "sha256": hashlib.sha256,
    "sha512": hashlib.sha512,
}

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: hash-file <file> [--md5|--sha1|--sha256|--sha512|--all]")
        print("  Default: --sha256")
        return
    filepath = args[0]
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    # Determine which algorithms
    algos = []
    if "--all" in args:
        algos = ["md5", "sha1", "sha256", "sha512"]
    else:
        for a in ["--md5", "--sha1", "--sha256", "--sha512"]:
            if a in args:
                algos.append(a[2:])  # remove --
    if not algos:
        algos = ["sha256"]  # default
    # Compute
    hashers = {name: HASH_ALGOS[name]() for name in algos if name in HASH_ALGOS}
    file_size = os.path.getsize(filepath)
    try:
        with open(filepath, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                for h in hashers.values():
                    h.update(chunk)
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)
    # Output
    print(f"File: {filepath}")
    print(f"Size: {file_size:,} bytes")
    print()
    for name in algos:
        if name in hashers:
            print(f"{name.upper():>6}: {hashers[name].hexdigest()}")

if __name__ == "__main__":
    main()
