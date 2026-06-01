#!/usr/bin/env python3
"""find-empty — Find empty directories and files recursively.

Usage: find-empty [--dir <path>] [--files] [--dirs] [--delete]

Scans a directory tree and reports empty files (0 bytes) and
empty directories (no entries, including no sub-directories).

Flags:
  --dir <path>   Root directory to scan (default: current dir)
  --files        Show only empty files
  --dirs         Show only empty directories
  --delete       Interactively delete each empty item found
  -h, --help     Show this help

Zero-dependency (stdlib only).
"""

import os
import sys


TOOL_META = {
    "name": "find-empty",
    "func": "main",
    "desc": "Find empty directories and files",
}


def _confirm(msg):
    """Prompt the user for yes/no confirmation. Returns True on 'y' or 'yes'."""
    try:
        resp = input(f"{msg} [y/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    return resp in ("y", "yes")


def _delete_path(path, is_dir):
    """Delete a file or empty directory, returning True on success."""
    try:
        if is_dir:
            os.rmdir(path)
        else:
            os.remove(path)
        return True
    except OSError as e:
        print(f"  Error deleting {path}: {e}", file=sys.stderr)
        return False


def _walk(root):
    """Walk root top-down, collecting empty dirs and empty files.

    Returns (empty_dirs, empty_files) — each entry is an absolute path.
    Works bottom-up so that a parent dir that becomes empty after child
    deletion is NOT reported (we report only originally-empty dirs).
    """
    empty_dirs = []
    empty_files = []

    for dirpath, dirnames, filenames in os.walk(root):
        # Check if this directory is empty (no subdirs, no files)
        if not dirnames and not filenames:
            empty_dirs.append(os.path.abspath(dirpath))
        else:
            # Check each file in this directory
            for fn in filenames:
                fp = os.path.join(dirpath, fn)
                try:
                    if os.path.getsize(fp) == 0:
                        empty_files.append(os.path.abspath(fp))
                except OSError:
                    pass

    return empty_dirs, empty_files


def main():
    args = sys.argv[1:]

    root = "."
    show_files = True
    show_dirs = True
    do_delete = False

    i = 0
    while i < len(args):
        a = args[i]
        if a in ("-h", "--help"):
            print(__doc__)
            return
        if a == "--dir" and i + 1 < len(args):
            root = args[i + 1]
            i += 2
            continue
        if a == "--files":
            show_dirs = False
            show_files = True
            i += 1
            continue
        if a == "--dirs":
            show_files = False
            show_dirs = True
            i += 1
            continue
        if a == "--delete":
            do_delete = True
            i += 1
            continue
        print(f"Unknown flag: {a}", file=sys.stderr)
        sys.exit(1)

    if not os.path.isdir(root):
        print(f"Error: not a directory: {root}", file=sys.stderr)
        sys.exit(1)

    empty_dirs, empty_files = _walk(root)

    found_any = False

    if show_dirs and empty_dirs:
        found_any = True
        print(f"Empty directories ({len(empty_dirs)}):")
        for d in empty_dirs:
            print(f"  [DIR]  {d}")
        print()

    if show_files and empty_files:
        found_any = True
        print(f"Empty files ({len(empty_files)}):")
        for f in empty_files:
            print(f"  [FILE] {f}")
        print()

    if not found_any:
        print("No empty directories or files found.")
        return

    if do_delete and show_dirs:
        print(f"--- Deleting empty directories ({len(empty_dirs)}) ---")
        for d in empty_dirs:
            if _confirm(f"  Delete empty directory: {d}"):
                if _delete_path(d, is_dir=True):
                    print(f"    Deleted: {d}")
            else:
                print(f"    Skipped: {d}")

    if do_delete and show_files:
        print(f"--- Deleting empty files ({len(empty_files)}) ---")
        for f in empty_files:
            if _confirm(f"  Delete empty file: {f}"):
                if _delete_path(f, is_dir=False):
                    print(f"    Deleted: {f}")
            else:
                print(f"    Skipped: {f}")


if __name__ == "__main__":
    main()
