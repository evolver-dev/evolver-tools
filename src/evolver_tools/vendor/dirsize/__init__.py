#!/usr/bin/env python3
"""dirsize — 目录空间分析器 / Directory disk usage analyzer.

Zero-dependency CLI that shows directory sizes sorted with human-readable output.
"""

import os
import sys
import argparse


def human_size(bytes_val: int) -> str:
    """Convert bytes to human-readable string."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(bytes_val) < 1024:
            return f"{bytes_val:>7.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:>7.1f} PB"


def calc_size(path: str) -> tuple[int, int]:
    """Calculate total size and file count. Returns (bytes, file_count)."""
    total = 0
    count = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            # Skip hidden dirs unless root
            if dirpath != path:
                dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    total += os.path.getsize(fp)
                    count += 1
                except OSError:
                    pass
    except PermissionError:
        pass
    return total, count


def scan_directory(path: str, max_depth: int = 1, top_n: int = 20,
                   min_size: int = 0, show_hidden: bool = False) -> list:
    """Scan directory and return sorted entries."""
    results = []
    base_depth = path.rstrip(os.sep).count(os.sep)

    for entry in os.scandir(path):
        if entry.name.startswith(".") and not show_hidden:
            continue
        try:
            if entry.is_dir(follow_symlinks=False):
                depth = entry.path.rstrip(os.sep).count(os.sep) - base_depth
                if depth < max_depth:
                    size, files = calc_size(entry.path)
                else:
                    # Estimate: don't recurse into deeper dirs
                    size = 0
                    files = 0
                    for f in os.scandir(entry.path):
                        try:
                            size += os.path.getsize(f.path)
                            files += 1
                        except OSError:
                            pass
                entry_type = "D"
            else:
                size = entry.stat().st_size
                files = 0
                entry_type = "F"

            if size >= min_size:
                results.append((entry.name, size, files, entry_type))
        except OSError:
            pass

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_n]


def entry():
    args = parse_args()

    if args.list:
        # List mode: show directory contents sorted by size
        results = scan_directory(
            args.path,
            max_depth=args.depth,
            top_n=args.top,
            min_size=args.min_size,
            show_hidden=args.all,
        )
        if not results:
            print(f"(empty or no entries >= {human_size(args.min_size)})")
            return

        # Find longest name for alignment
        name_width = max(len(r[0]) for r in results)
        name_width = min(name_width, 50)
        name_width = max(name_width, 20)

        print(f"   TYPE  {'NAME'.ljust(name_width)}  {'SIZE'.rjust(10)}  {'FILES'.rjust(5)}")
        print(f"   {'----' * ((name_width // 4) + 5)}")
        total_size = 0
        total_files = 0
        for name, size, files, etype in results:
            print(f"   [{etype}]  {name.ljust(name_width)}  {human_size(size)}  {files:>5}")
            total_size += size
            total_files += files
        print(f"   {'----' * ((name_width // 4) + 5)}")
        print(f"   Total:  {human_size(total_size)}  in {total_files} files")
        return

    # Single path mode
    if not os.path.exists(args.path):
        print(f"Error: path not found: {args.path}", file=sys.stderr)
        sys.exit(1)

    if os.path.isfile(args.path):
        size = os.path.getsize(args.path)
        print(f"{human_size(size)}  {args.path}")
    else:
        size, files = calc_size(args.path)
        print(f"{human_size(size)}  {args.path}  ({files} files)")


def parse_args():
    parser = argparse.ArgumentParser(
        description="dirsize — 目录空间分析器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  dirsize                          # Show current dir size
  dirsize /home                    # Show /home size
  dirsize --list ~/Projects        # List Projects contents sorted by size
  dirsize --list --depth 2 --top 10  # Top 10 dirs, 2 levels deep
  dirsize --list --min-size 1MB    # Only entries >= 1 MB
  dirsize --list --all             # Include hidden dirs/files
""")
    parser.add_argument("path", nargs="?", default=".",
                        help="Directory or file to analyze (default: .)")
    parser.add_argument("-l", "--list", action="store_true",
                        help="List directory contents sorted by size")
    parser.add_argument("-d", "--depth", type=int, default=1,
                        help="Max recursion depth for --list (default: 1)")
    parser.add_argument("-t", "--top", type=int, default=20,
                        help="Number of entries to show (default: 20)")
    parser.add_argument("-m", "--min-size", type=str, default="0",
                        help=f"Minimum size filter like 1MB, 500KB (default: 0)")
    parser.add_argument("-a", "--all", action="store_true",
                        help="Include hidden files/dirs")

    args = parser.parse_args()

    # Parse min-size
    if args.min_size and args.min_size != "0":
        args.min_size = parse_size(args.min_size)
    else:
        args.min_size = 0

    return args


def parse_size(s: str) -> int:
    """Parse size string like '1MB', '500KB', '2GB' to bytes."""
    s = s.strip().upper()
    units = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}
    for suffix, multiplier in units.items():
        if s.endswith(suffix):
            try:
                num = float(s[: -len(suffix)])
                return int(num * multiplier)
            except ValueError:
                break
    # Try parsing as plain number (bytes)
    try:
        return int(s)
    except ValueError:
        print(f"Warning: invalid size '{s}', using 0", file=sys.stderr)
        return 0



# === Auto-registration metadata ===
TOOL_META = {
    "name": "dirsize",
    "func": "entry",
    "desc": 'Dirsize',
}

if __name__ == "__main__":
    entry()
