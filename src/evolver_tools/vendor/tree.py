#!/usr/bin/env python3
"""tree — Directory tree viewer with branch characters and indentation."""

import os
import sys

TOOL_META = {
    "name": "tree",
    "func": "main",
    "desc": "Display directory tree. Usage: tree [path] [--max-depth N] [--dirs-only]",
}


def walk_tree(root_path, max_depth=None, dirs_only=False, prefix="", depth=0):
    """Recursively walk and print directory tree."""
    if max_depth is not None and depth > max_depth:
        return

    try:
        entries = sorted(os.listdir(root_path))
    except PermissionError:
        print(f"{prefix}  [Permission Denied]")
        return
    except OSError as e:
        print(f"{prefix}  [Error: {e}]")
        return

    # Separate dirs and files
    dirs = []
    files = []
    for e in entries:
        full = os.path.join(root_path, e)
        if e.startswith("."):
            continue  # skip hidden
        try:
            if os.path.isdir(full):
                dirs.append(e)
            else:
                files.append(e)
        except OSError:
            pass

    items = dirs
    if not dirs_only:
        items.extend(files)

    for i, name in enumerate(items):
        full = os.path.join(root_path, name)
        is_last = i == len(items) - 1
        is_dir = name in dirs

        connector = "└── " if is_last else "├── "
        print(f"{prefix}{connector}{name}")

        if is_dir:
            extension = "    " if is_last else "│   "
            walk_tree(full, max_depth, dirs_only,
                      prefix + extension, depth + 1)


def main():
    args = sys.argv[1:]

    path = "."
    max_depth = None
    dirs_only = False

    # Extract optional flags
    filtered = []
    i = 0
    while i < len(args):
        if args[i] == "--max-depth" and i + 1 < len(args):
            try:
                max_depth = int(args[i + 1])
            except ValueError:
                print("Error: --max-depth requires an integer", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--dirs-only":
            dirs_only = True
            i += 1
        elif args[i] in ("-h", "--help"):
            print("Usage: tree [path] [--max-depth N] [--dirs-only]")
            print()
            print("Options:")
            print("  path              Directory to display (default: current dir)")
            print("  --max-depth N     Limit recursion depth")
            print("  --dirs-only       Show directories only")
            return
        else:
            filtered.append(args[i])
            i += 1

    if filtered:
        path = filtered[0]

    if not os.path.isdir(path):
        print(f"Error: not a directory: {path}", file=sys.stderr)
        sys.exit(1)

    print(path)
    walk_tree(path, max_depth, dirs_only)


if __name__ == "__main__":
    main()
