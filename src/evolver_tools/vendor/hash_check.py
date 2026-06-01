#!/usr/bin/env python3
"""hash_check — Compare file hashes against known values."""

import sys
import hashlib
import os

TOOL_META = {
    "name": "hash_check",
    "func": "main",
    "desc": "Compare file hashes against known SHA256/MD5 values",
}


def file_hash(path, algo="sha256"):
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print("Usage: evolver hash_check <file> [expected_hash]")
        print("       evolver hash_check --algo <algo> <file> [expected_hash]")
        print()
        print("Algorithms: md5, sha1, sha256 (default), sha512")
        return

    algo = "sha256"
    files = []
    for a in args:
        if a.startswith("--algo="):
            algo = a.split("=", 1)[1]
        elif a in ("--algo", "-a"):
            continue
        elif algo in ("--algo", "-a"):
            algo = a
        else:
            files.append(a)

    expected = None
    if len(files) > 1 and not files[1].startswith("--"):
        expected = files[1]
        files = [files[0]]

    if not files:
        print("Error: no file specified")
        return 1

    path = files[0]
    if not os.path.exists(path):
        print(f"Error: file not found: {path}")
        return 1

    actual = file_hash(path, algo)

    if expected:
        if actual == expected.lower():
            print(f"\033[32m✓ MATCH\033[0m ({algo})")
        else:
            print(f"\033[31m✗ MISMATCH\033[0m ({algo})")
            print(f"  Expected: {expected}")
            print(f"  Actual:   {actual}")
            return 1
    else:
        print(f"{algo.upper()}: {actual}  {os.path.basename(path)}")


if __name__ == "__main__":
    sys.exit(main() or 0)
