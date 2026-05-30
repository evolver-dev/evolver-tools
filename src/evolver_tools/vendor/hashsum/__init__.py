"""hashsum: Zero-dependency checksum tool (MD5, SHA1, SHA256, SHA512, BLAKE2).

Pure Python stdlib implementation (hashlib). Works like sha256sum/md5sum/b2sum.
"""

import sys
import os
import hashlib
from pathlib import Path


__version__ = "1.0.0"

# Available algorithms mapped to their hashlib names
ALGORITHMS = {
    "md5": hashlib.md5,
    "sha1": hashlib.sha1,
    "sha224": hashlib.sha224,
    "sha256": hashlib.sha256,
    "sha384": hashlib.sha384,
    "sha512": hashlib.sha512,
    "blake2b": hashlib.blake2b,
    "blake2s": hashlib.blake2s,
    "sha3_256": hashlib.sha3_256,
    "sha3_512": hashlib.sha3_512,
}


CHUNK_SIZE = 65536  # 64KB


def hash_file(path: str, alg: str) -> tuple:
    """Hash a single file, return (hexdigest, path)."""
    h = ALGORITHMS[alg]()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest(), path


def hash_stdin(alg: str) -> str:
    """Hash stdin data."""
    h = ALGORITHMS[alg]()
    while True:
        chunk = sys.stdin.buffer.read(CHUNK_SIZE)
        if not chunk:
            break
        h.update(chunk)
    return h.hexdigest()


def format_line(hexdigest: str, path: str, binary: bool) -> str:
    """Format output line like sha256sum."""
    marker = " *" if binary else "  "
    return f"{hexdigest}{marker}{path}"


def check_file(ck_path: str, alg: str = "sha256", strict: bool = False) -> tuple:
    """Verify checksums from a checksum file. Returns (passed, failed, missing)."""
    passed = []
    failed = []
    missing = []

    with open(ck_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Parse: HEX  MODE?  PATH
            parts = line.split(None, 2)
            if len(parts) < 2:
                continue

            exp_hex = parts[0]
            rest = parts[-1]  # path (skip binary marker)

            if os.path.exists(rest):
                actual_hex, _ = hash_file(rest, alg)
                if actual_hex == exp_hex:
                    passed.append(rest)
                else:
                    failed.append(rest)
            else:
                missing.append(rest)

    return passed, failed, missing


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="hashsum — Checksum calculator and verifier",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  hashsum file.iso                          # Default: SHA256
  hashsum -a md5 file.zip                   # MD5
  hashsum -a sha512 file.bin                # SHA512
  hashsum -a blake2b file.tar.gz            # BLAKE2b
  hashsum *.iso > checksums.sha256          # Generate checksum file
  hashsum -c checksums.sha256               # Verify checksums
  cat file.bin | hashsum                    # Hash from stdin
  hashsum -a md5 -r file.txt                # Just the hash (no filename)
        """
    )
    parser.add_argument("files", nargs="*", help="Files to hash (default: stdin)")
    parser.add_argument("-a", "--algorithm", default="sha256",
                        choices=sorted(ALGORITHMS.keys()),
                        help="Hash algorithm (default: sha256)")
    parser.add_argument("-c", "--check", action="store_true",
                        help="Read checksums from file and verify")
    parser.add_argument("-b", "--binary", action="store_true",
                        help="Binary mode marker (*) in output")
    parser.add_argument("-r", "--raw", action="store_true",
                        help="Output raw hash only (no filename)")
    parser.add_argument("-l", "--list", action="store_true",
                        help="List available algorithms")

    args = parser.parse_args()

    # Allow algorithm as first positional arg (e.g. `hashsum sha256 file.txt`)
    if args.files and args.files[0] in ALGORITHMS:
        args.algorithm = args.files[0]
        args.files = args.files[1:]

    # List algorithms
    if args.list:
        print("Available algorithms:")
        for name in sorted(ALGORITHMS.keys()):
            desc = hashlib.algorithms_available if hasattr(hashlib, 'algorithms_available') else ""
            size = hashlib.new(name).digest_size * 8 if name not in ALGORITHMS else ""
            print(f"  {name:<12} {hashlib.new(name).digest_size * 8} bits")
        return

    # Check mode
    if args.check:
        total_pass = 0
        total_fail = 0
        total_miss = 0
        for ck_file in args.files or [sys.stdin]:
            if ck_file == sys.stdin:
                # Read from stdin
                import io
                for line in sys.stdin:
                    pass  # Skip for now, proper check file stdin not implemented yet
                continue
            passed, failed, missing = check_file(ck_file, args.algorithm)
            for p in passed:
                print(f"{p}: OK")
            for f in failed:
                print(f"{f}: FAILED")
            for m in missing:
                print(f"{m}: MISSING")
            total_pass += len(passed)
            total_fail += len(failed)
            total_miss += len(missing)
            if not (passed or failed or missing):
                print(f"hashsum: {ck_file}: no valid checksum lines found", file=sys.stderr)

        if total_fail + total_miss > 0:
            print(f"\nChecksums: {total_pass} passed, {total_fail} failed, {total_miss} missing")
            sys.exit(1)
        else:
            print(f"\nChecksums: {total_pass} passed")
        return

    # Hash mode
    if not args.files:
        # Hash from stdin
        hexdigest = hash_stdin(args.algorithm)
        if args.raw:
            print(hexdigest)
        else:
            print(format_line(hexdigest, "-", args.binary))
        return

    # Hash files
    results = []
    errors = []
    for path in args.files:
        if not os.path.exists(path):
            errors.append(f"hashsum: {path}: No such file or directory")
            continue
        try:
            hexdigest, _ = hash_file(path, args.algorithm)
            results.append((hexdigest, path))
        except (IOError, PermissionError) as e:
            errors.append(f"hashsum: {path}: {e}")

    # Print errors first (like sha256sum does)
    for err in errors:
        print(err, file=sys.stderr)

    # Print results
    for hexdigest, path in results:
        if args.raw:
            print(hexdigest)
        else:
            print(format_line(hexdigest, path, args.binary))

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
