#!/usr/bin/env python3
"""disk-cleanup — Analyze disk usage and suggest cleanup actions."""
import os
import sys

TOOL_META = {
    "name": "disk-cleanup",
    "func": "main",
    "desc": "Analyze disk usage and suggest cleanup. Usage: disk-cleanup [path] [--deep]",
}

COMMON_CLEANUP = [
    ("~/.cache", "Cache files"),
    ("~/.local/share/Trash", "Trash"),
    ("/tmp", "Temp files"),
    ("~/.npm/_cacache", "npm cache"),
    ("~/.rustup/tmp", "rustup temp"),
    ("~/.cargo/registry/cache", "Cargo cache"),
    ("~/.gradle/caches", "Gradle cache"),
    ("~/.m2/repository", "Maven cache"),
    ("~/.local/share/pip/cache", "pip cache"),
]

def get_size(path):
    try:
        if os.path.isfile(path):
            return os.path.getsize(path)
        total = 0
        for root, dirs, files in os.walk(path):
            for f in files:
                try:
                    total += os.path.getsize(os.path.join(root, f))
                except Exception:
                    pass
        return total
    except Exception:
        return 0

def format_size(size):
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

def find_large_files(path, limit=20, min_mb=50):
    large = []
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if not d.startswith(".") or d == "."]
        for f in files:
            try:
                fp = os.path.join(root, f)
                size = os.path.getsize(fp)
                if size >= min_mb * 1024 * 1024:
                    large.append((fp, size))
            except Exception:
                pass
    large.sort(key=lambda x: -x[1])
    return large[:limit]

def main():
    args = sys.argv[1:]
    root_path = args[0] if args and not args[0].startswith("-") else os.path.expanduser("~")
    deep = "--deep" in args
    root_path = os.path.abspath(root_path)
    print(f"Disk Cleanup Analysis: {root_path}")
    print("=" * 50)
    # Check common cleanup locations
    print("\nCommon cleanup locations:")
    any_found = False
    for rel_path, label in COMMON_CLEANUP:
        path = os.path.expanduser(rel_path)
        if os.path.exists(path):
            size = get_size(path)
            if size > 0:
                any_found = True
                print(f"  {format_size(size):>8}  {label} ({path})")
    if not any_found:
        print("  (none found)")
    # Check directory sizes if root path is a directory
    if os.path.isdir(root_path):
        print(f"\nLargest directories in {root_path}:")
        dirs = []
        for entry in os.listdir(root_path):
            full = os.path.join(root_path, entry)
            if os.path.isdir(full):
                size = get_size(full)
                dirs.append((entry, size))
        dirs.sort(key=lambda x: -x[1])
        for name, size in dirs[:10]:
            if size > 1024 * 1024:  # > 1MB
                print(f"  {format_size(size):>8}  {name}")
    if deep:
        print(f"\nLargest files (>50MB):")
        large = find_large_files(root_path)
        if large:
            for fp, size in large:
                rel = os.path.relpath(fp, os.path.expanduser("~"))
                print(f"  {format_size(size):>8}  ~/{rel}")
        else:
            print("  (none found)")
    print("\nSuggestions:")
    print("  temp-cleaner --dry-run    Preview temp file cleanup")
    print("  disk-usage                Show disk usage summary")

if __name__ == "__main__":
    main()
