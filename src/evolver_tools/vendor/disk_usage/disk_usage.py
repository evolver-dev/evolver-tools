#!/usr/bin/env python3
"""disk-usage — Disk usage analyzer (du / df on steroids)

Analyze disk usage by directory, largest files, and summary.

Usage:
    disk-usage                   # Current directory summary
    disk-usage /path/to/dir      # Specific directory
    disk-usage --depth=1         # Show top-level subdirs only
    disk-usage --top=10          # Show top 10 largest items
    disk-usage --files           # Show largest files (not dirs)
    disk-usage --all             # Show everything
    disk-usage --human           # Human-readable (default)
    disk-usage --bytes           # Raw bytes
"""
import sys
import os


def format_size(bytes_val, human=True):
    """Format byte size to human-readable."""
    if not human:
        return str(bytes_val)
    for unit in ('B', 'K', 'M', 'G', 'T', 'P'):
        if abs(bytes_val) < 1024:
            return f"{bytes_val:.1f}{unit}" if isinstance(bytes_val, float) else f"{bytes_val}{unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f}P"


def get_size(path, follow_links=False):
    """Get total size of file or directory."""
    if os.path.isfile(path) or os.path.islink(path):
        try:
            return os.path.getsize(path)
        except OSError:
            return 0
    total = 0
    try:
        with os.scandir(path) as it:
            for entry in it:
                try:
                    if entry.is_file(follow_symlinks=follow_links):
                        total += entry.stat(follow_symlinks=follow_links).st_size
                    elif entry.is_dir(follow_symlinks=follow_links):
                        total += get_size(entry.path, follow_links)
                except PermissionError:
                    continue
                except OSError:
                    continue
    except PermissionError:
        pass
    except OSError:
        pass
    return total


def gather_items(path, max_depth=0, current_depth=0, include_files=False):
    """Gather directory entries with sizes."""
    items = []

    try:
        with os.scandir(path) as it:
            for entry in it:
                try:
                    if entry.is_file() or entry.is_symlink():
                        size = entry.stat().st_size
                        items.append((entry.path, size, 'file'))
                    elif entry.is_dir():
                        size = get_size(entry.path)
                        items.append((entry.path, size, 'dir'))
                        if max_depth > 0 and current_depth < max_depth:
                            items.extend(gather_items(entry.path, max_depth, current_depth + 1, include_files))
                except PermissionError:
                    continue
                except OSError:
                    continue
    except PermissionError:
        pass

    return items


def main():
    args = sys.argv[1:]

    if not args or args[0] in ('-h', '--help'):
        print(__doc__.strip())
        return

    target = None
    depth = 0
    top_n = 20
    human = True
    show_all = False
    show_files = False

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == '--depth':
            i += 1
            if i < len(args):
                depth = int(args[i])
        elif arg.startswith('--depth='):
            depth = int(arg.split('=', 1)[1])
        elif arg == '--top':
            i += 1
            if i < len(args):
                top_n = int(args[i])
        elif arg.startswith('--top='):
            top_n = int(arg.split('=', 1)[1])
        elif arg == '--bytes':
            human = False
        elif arg == '--human':
            human = True
        elif arg == '--all':
            show_all = True
        elif arg == '--files':
            show_files = True
        elif arg == '--dirs':
            show_files = False
        elif arg.startswith('-'):
            print(f"Error: unknown option '{arg}'", file=sys.stderr)
            sys.exit(1)
        else:
            target = arg
        i += 1

    if not target:
        target = '.'

    if not os.path.exists(target):
        print(f"Error: path not found: {target}", file=sys.stderr)
        sys.exit(1)

    if os.path.isfile(target):
        size = os.path.getsize(target)
        print(f"{format_size(size, human):>10}  {target}")
        return

    # Scan directory
    max_d = depth if depth > 0 else 0
    print(f"Scanning: {target}")
    items = gather_items(target, max_depth=max_d, include_files=show_files or show_all)

    if not items:
        print("(empty or no permission)")
        return

    # Sort by size (descending)
    items.sort(key=lambda x: x[1], reverse=True)

    # Filter by type
    if not show_all:
        if show_files:
            items = [i for i in items if i[2] == 'file']
        else:
            items = [i for i in items if i[2] == 'dir']

    # Apply limit
    display_items = items[:top_n]

    print(f"{'Size':>10}  {'Type':<4}  {'Path'}")
    print(f"{'-'*10}  {'-'*4}  {'-'*60}")
    total_size = sum(i[1] for i in items)
    for path, size, itype in display_items:
        rel_path = os.path.relpath(path, target) if path != target else '.'
        print(f"{format_size(size, human):>10}  {itype:<4}  {rel_path}")

    print()
    print(f"Total: {format_size(total_size, human)} in {len(items)} items")


if __name__ == '__main__':
    main()
