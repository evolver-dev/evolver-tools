#!/usr/bin/env python3
"""checksum-dir — Generate/verify checksums for all files in a directory."""
import sys
import os
import argparse
import hashlib
import json


ALGORITHMS = {
    "md5": hashlib.md5,
    "sha1": hashlib.sha1,
    "sha256": hashlib.sha256,
    "sha512": hashlib.sha512,
    "sha224": hashlib.sha224,
    "sha384": hashlib.sha384,
}


def get_checksum(filepath, algorithm="sha256"):
    """Compute the checksum of a file."""
    if algorithm not in ALGORITHMS:
        print(f"Error: Unsupported algorithm '{algorithm}'. Supported: {', '.join(ALGORITHMS.keys())}",
              file=sys.stderr)
        sys.exit(1)
    h = ALGORITHMS[algorithm]()
    try:
        with open(filepath, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                h.update(chunk)
    except IOError as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
        return None
    return h.hexdigest()


def collect_files(directory, recursive=False, exclude_patterns=None,
                  include_patterns=None, follow_symlinks=False):
    """Collect all files in a directory."""
    if not os.path.isdir(directory):
        print(f"Error: Directory not found: {directory}", file=sys.stderr)
        sys.exit(1)

    files = []
    try:
        if recursive:
            for root, dirnames, filenames in os.walk(directory, followlinks=follow_symlinks):
                for fname in sorted(filenames):
                    fpath = os.path.join(root, fname)
                    rel_path = os.path.relpath(fpath, directory)
                    files.append((rel_path, fpath))
        else:
            for entry in sorted(os.listdir(directory)):
                fpath = os.path.join(directory, entry)
                if os.path.isfile(fpath) or (follow_symlinks and os.path.islink(fpath)):
                    files.append((entry, fpath))
    except OSError as e:
        print(f"Error scanning directory: {e}", file=sys.stderr)
        sys.exit(1)

    # Filter out the checksums file itself
    checksum_filename = os.path.basename(directory) + ".checksums"
    files = [(name, path) for name, path in files if name != checksum_filename]

    return files


def format_checksum_line(checksum, filename, algorithm="sha256"):
    """Format a line in sha256sum-compatible format."""
    return f"{checksum}  {filename}"


def cmd_generate(directory, algorithm, output_file, recursive, verbose):
    """Generate checksums for all files in directory."""
    files = collect_files(directory, recursive=recursive)

    if not files:
        print("No files found.")
        return

    lines = []
    total = len(files)
    errors = 0

    for i, (rel_path, abs_path) in enumerate(files, 1):
        if verbose:
            print(f"[{i}/{total}] {rel_path}...", file=sys.stderr, end="\r")

        checksum = get_checksum(abs_path, algorithm)
        if checksum is None:
            errors += 1
            continue

        line = format_checksum_line(checksum, rel_path, algorithm)
        lines.append(line)

    if verbose:
        print("\n", file=sys.stderr)

    output_content = "\n".join(lines) + "\n"

    if output_file:
        try:
            with open(output_file, "w") as f:
                f.write(output_content)
            print(f"Written {len(lines)} checksums to {output_file}")
        except IOError as e:
            print(f"Error writing {output_file}: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(output_content, end="")

    if errors:
        print(f"Warning: {errors} file(s) had errors", file=sys.stderr)


def parse_checksums_file(checksums_path):
    """Parse a checksums file (sha256sum format or custom format)."""
    if not os.path.isfile(checksums_path):
        print(f"Error: Checksums file not found: {checksums_path}", file=sys.stderr)
        sys.exit(1)

    entries = {}
    algorithm = "sha256"

    try:
        with open(checksums_path, "r") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Try sha256sum format: <checksum>  <filename>
                # Two spaces separate checksum from filename
                if "  " in line:
                    parts = line.split("  ", 1)
                    if len(parts) == 2:
                        checksum, filename = parts[0].strip(), parts[1].strip()
                        # Detect algorithm from checksum length
                        if len(checksum) == 32:
                            algorithm = "md5"
                        elif len(checksum) == 40:
                            algorithm = "sha1"
                        elif len(checksum) == 64:
                            algorithm = "sha256"
                        elif len(checksum) == 128:
                            algorithm = "sha512"
                        elif len(checksum) == 56:
                            algorithm = "sha224"
                        elif len(checksum) == 96:
                            algorithm = "sha384"
                        entries[filename] = checksum
                        continue

                # Try <algorithm>:<checksum>  <filename>
                if ":" in line:
                    first_part = line.split()[0] if line.split() else ""
                    if ":" in first_part:
                        alg, chk = first_part.split(":", 1)
                        if alg in ALGORITHMS:
                            algorithm = alg
                            filename_part = " ".join(line.split()[1:])
                            if "  " in line:
                                filename_part = line.split("  ", 1)[1] if "  " in line else " ".join(line.split()[1:])
                            entries[filename_part] = chk
                            continue
    except IOError as e:
        print(f"Error reading {checksums_path}: {e}", file=sys.stderr)
        sys.exit(1)

    return algorithm, entries


def cmd_verify(checksums_path, directory, verbose):
    """Verify checksums against a checksums file."""
    algorithm, expected = parse_checksums_file(checksums_path)

    # Determine base directory
    base_dir = directory or os.path.dirname(os.path.abspath(checksums_path))

    if not os.path.isdir(base_dir):
        print(f"Error: Directory not found: {base_dir}", file=sys.stderr)
        sys.exit(1)

    total = len(expected)
    passed = 0
    failed = 0
    missing = 0

    print(f"Verifying {total} checksums using {algorithm}...")
    print()

    for filename, expected_checksum in sorted(expected.items()):
        filepath = os.path.join(base_dir, filename)
        if not os.path.isfile(filepath):
            print(f"  \033[31mMISSING\033[0m {filename}")
            missing += 1
            continue

        actual_checksum = get_checksum(filepath, algorithm)
        if actual_checksum is None:
            failed += 1
            continue

        if actual_checksum == expected_checksum:
            if verbose:
                print(f"  \033[32mOK\033[0m      {filename}")
            passed += 1
        else:
            print(f"  \033[31mFAIL\033[0m    {filename}")
            if verbose:
                print(f"          Expected: {expected_checksum}")
                print(f"          Actual:   {actual_checksum}")
            failed += 1

    print()
    print(f"Results: {passed} passed, {failed} failed, {missing} missing (of {total})")

    if failed > 0 or missing > 0:
        sys.exit(1)


def cmd_diff(directory, other_dir, algorithm, recursive, verbose):
    """Compare checksums between two directories."""
    files1 = collect_files(directory, recursive=recursive)
    files2 = collect_files(other_dir, recursive=recursive)

    map1 = {name: get_checksum(path, algorithm) for name, path in files1}
    map2 = {name: get_checksum(path, algorithm) for name, path in files2}

    names1 = set(map1.keys())
    names2 = set(map2.keys())

    only_in_1 = names1 - names2
    only_in_2 = names2 - names1
    common = names1 & names2

    different = {n for n in common if map1[n] != map2[n]}

    if only_in_1:
        print(f"Only in {directory}:")
        for n in sorted(only_in_1):
            print(f"  - {n}")

    if only_in_2:
        print(f"Only in {other_dir}:")
        for n in sorted(only_in_2):
            print(f"  + {n}")

    if different:
        print(f"Different files ({len(different)}):")
        for n in sorted(different):
            print(f"  ~ {n}")

    if not only_in_1 and not only_in_2 and not different:
        print("Directories are identical.")


def main():
    parser = argparse.ArgumentParser(
        description="Generate/verify checksums for all files in a directory."
    )
    parser.add_argument("directory", nargs="?", help="Directory to checksum")
    parser.add_argument("--algorithm", "-a", default="sha256",
                        choices=list(ALGORITHMS.keys()),
                        help="Hash algorithm (default: sha256)")
    parser.add_argument("--output", "-o", help="Output file for checksums")
    parser.add_argument("--verify", "-v", metavar="CHECKSUMS_FILE",
                        help="Verify against a checksums file")
    parser.add_argument("--recursive", "-r", action="store_true",
                        help="Process subdirectories recursively")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--diff", nargs=2, metavar=("DIR1", "DIR2"),
                        help="Compare checksums between two directories")

    args = parser.parse_args()

    try:
        if args.verify:
            cmd_verify(args.verify, args.directory, args.verbose)
        elif args.diff:
            dir1, dir2 = args.diff
            cmd_diff(dir1, dir2, args.algorithm, args.recursive, args.verbose)
        elif args.directory:
            cmd_generate(args.directory, args.algorithm, args.output,
                         args.recursive, args.verbose)
        else:
            parser.print_help()
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
