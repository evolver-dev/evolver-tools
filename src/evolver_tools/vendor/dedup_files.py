#!/usr/bin/env python3
"""dedup-files — Find and optionally remove duplicate files by SHA256 content hash.

Scans a directory recursively, groups files by their SHA256 hash,
and reports duplicates. Supports interactive deletion.

Usage:
    dedup-files --dir /path/to/scan
    dedup-files --dir . --min-size 1024
    dedup-files --dir . --delete
    dedup-files --dir . --delete --dry-run

Options:
    --dir DIR       Directory to scan (default: .)
    --min-size N    Minimum file size in bytes (default: 0)
    --delete        Interactively delete duplicate files
    --dry-run       Show what would be deleted without actually deleting
    -h, --help      Show this help message
"""

import sys
import os
import hashlib
import argparse

TOOL_META = {
    "name": "dedup-files",
    "func": "main",
    "desc": "Find and optionally delete duplicate files by SHA256 hash",
}


def sha256_file(path: str, chunk_size: int = 65536) -> str:
    """Compute SHA256 hash of a file, reading in chunks to handle large files."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def scan_directory(directory: str, min_size: int = 0):
    """Scan directory recursively, returning (hashes_dict, error_count).

    hashes dict is {sha256: [filepaths]}.
    Skips symlinks and files smaller than min_size.
    """
    hashes: dict[str, list[str]] = {}
    errors = 0

    for root, dirs, files in os.walk(directory, followlinks=False):
        for filename in files:
            path = os.path.join(root, filename)

            # Skip symlinks
            if os.path.islink(path):
                continue

            try:
                stat = os.stat(path)
                if stat.st_size < min_size:
                    continue

                file_hash = sha256_file(path)
                if file_hash not in hashes:
                    hashes[file_hash] = []
                hashes[file_hash].append(path)

            except (OSError, PermissionError) as e:
                print(f"Warning: cannot read {path}: {e}", file=sys.stderr)
                errors += 1

    return hashes, errors


def human_size(size):
    """Format byte count to human-readable string."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


def prompt_yes_no(prompt: str) -> bool:
    """Prompt user for yes/no input. Returns True for 'y' or 'yes'."""
    while True:
        try:
            response = input(prompt + " [y/N] ").strip().lower()
            if response in ("y", "yes"):
                return True
            if response in ("n", "no", ""):
                return False
        except (EOFError, KeyboardInterrupt):
            print()
            return False


def report_duplicates(hash_groups: dict, min_size: int, delete: bool, dry_run: bool) -> int:
    """Report duplicate file groups and optionally delete.

    Returns total bytes that would be/were saved.
    """
    # Filter to only groups with duplicates
    dup_groups = {h: paths for h, paths in hash_groups.items() if len(paths) > 1}

    if not dup_groups:
        if min_size > 0:
            print(f"No duplicate files found (minimum size: {human_size(min_size)}).")
        else:
            print("No duplicate files found.")
        return 0

    total_duplicates = sum(len(paths) - 1 for paths in dup_groups.values())
    total_wasted_bytes = 0
    deleted_count = 0

    print(f"\nFound {len(dup_groups)} set(s) of duplicates ({total_duplicates} extra file(s)):\n")

    for hash_val, paths in sorted(dup_groups.items(), key=lambda x: x[1][0]):
        size = os.path.getsize(paths[0])
        wasted = size * (len(paths) - 1)
        total_wasted_bytes += wasted

        print(f"  Hash: {hash_val[:16]}...  Size: {human_size(size)}  ({len(paths)} copies, {human_size(wasted)} wasted)")
        for i, path in enumerate(paths):
            keep_marker = " (kept)" if i == 0 and delete else ""
            print(f"    {i + 1}. {path}{keep_marker}")
        print()

        if not delete:
            continue

        # Interactive deletion: keep the first file, ask about rest
        for path in paths[1:]:
            rel = os.path.relpath(path, os.getcwd()) if os.getcwd() else path
            if dry_run:
                print(f"  [DRY-RUN] Would delete: {rel}")
                deleted_count += 1
            else:
                if prompt_yes_no(f"  Delete duplicate '{rel}' ({human_size(size)})?"):
                    try:
                        os.remove(path)
                        print(f"  Deleted: {rel}")
                        deleted_count += 1
                    except OSError as e:
                        print(f"  Error deleting {rel}: {e}", file=sys.stderr)
                else:
                    print(f"  Skipped: {rel}")

    if delete and not dry_run:
        print(f"\nDeleted {deleted_count} file(s).")
    elif delete and dry_run:
        print(f"\n[DRY-RUN] Would delete {deleted_count} file(s).")

    return total_wasted_bytes


def main():
    parser = argparse.ArgumentParser(
        description="Find and optionally remove duplicate files by SHA256 content hash.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  dedup-files --dir /path/to/scan\n"
            "  dedup-files --dir . --min-size 1024\n"
            "  dedup-files --dir . --delete\n"
            "  dedup-files --dir . --delete --dry-run\n"
        ),
    )
    parser.add_argument("--dir", default=".", help="Directory to scan (default: .)")
    parser.add_argument("--min-size", type=int, default=0, help="Minimum file size in bytes")
    parser.add_argument("--delete", action="store_true", help="Interactively delete duplicate files")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without deleting")
    args = parser.parse_args()

    directory = os.path.abspath(args.dir)

    if not os.path.isdir(directory):
        print(f"Error: directory not found: {directory}", file=sys.stderr)
        sys.exit(1)

    if args.min_size < 0:
        print("Error: --min-size must be non-negative", file=sys.stderr)
        sys.exit(1)

    # Confirm --delete interactive mode
    if args.delete and not args.dry_run:
        print(f"Scanning: {directory}")
        print("WARNING: --delete mode is interactive. You will be prompted before each deletion.")

    print(f"Scanning directory: {directory}")
    if args.min_size > 0:
        print(f"Minimum file size: {human_size(args.min_size)}")

    hashes, errors = scan_directory(directory, min_size=args.min_size)

    if errors > 0:
        print(f"(Encountered {errors} error(s) during scan)")

    if not hashes:
        print("No files found.")
        return

    wasted = report_duplicates(hashes, args.min_size, delete=args.delete, dry_run=args.dry_run)

    if not args.delete:
        print(f"\nTotal wasted space: {human_size(wasted)}")
        if wasted > 0:
            print("Use --delete to interactively remove duplicates.")


if __name__ == "__main__":
    main()
