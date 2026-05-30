#!/usr/bin/env python3
"""backup — File/directory backup with rotation.

Usage: backup <source> [--dest=<dir>] [--keep=N]
       backup <source1> <source2> --dest=backups/ [--keep=5]

Creates timestamped backups. Keeps last N versions by default.
Zero-dependency (stdlib only).
"""

import sys, os, shutil, time, glob, re
from datetime import datetime

def get_timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def backup_path(src, dest, ts):
    base = os.path.basename(os.path.normpath(src.rstrip('/')))
    backup_name = f"{base}.{ts}.bak"
    return os.path.join(dest, backup_name)

def rotate_backups(dest, pattern, keep):
    files = sorted(glob.glob(os.path.join(dest, pattern)))
    while len(files) > keep:
        oldest = files.pop(0)
        if os.path.isdir(oldest):
            shutil.rmtree(oldest)
        else:
            os.remove(oldest)
        print(f"  Removed old backup: {oldest}", file=sys.stderr)

def main():
    args = sys.argv[1:]
    if not args or '-h' in args or '--help' in args:
        print(__doc__)
        return

    dest = '.'
    keep = 5
    sources = []

    for a in args:
        if a.startswith('--dest='):
            dest = a.split('=', 1)[1]
        elif a.startswith('--keep='):
            keep = int(a.split('=', 1)[1])
        elif not a.startswith('-'):
            sources.append(a)

    if not sources:
        print("Error: at least one source required", file=sys.stderr)
        sys.exit(1)

    os.makedirs(dest, exist_ok=True)
    ts = get_timestamp()

    for src in sources:
        if not os.path.exists(src):
            print(f"  Skipping (not found): {src}", file=sys.stderr)
            continue
        dst = backup_path(src, dest, ts)
        is_dir = os.path.isdir(src)
        try:
            if is_dir:
                shutil.copytree(src, dst, symlinks=True)
            else:
                shutil.copy2(src, dst)
            file_type = "directory" if is_dir else "file"
            print(f"  Backed up: {src} → {dst}  [{file_type}]")

            # Rotate
            base = os.path.basename(os.path.normpath(src.rstrip('/')))
            pattern = f"{base}.*.bak"
            rotate_backups(dest, pattern, keep)
        except Exception as e:
            print(f"  Error backing up {src}: {e}", file=sys.stderr)


# === Auto-registration metadata ===
TOOL_META = {
    "name": "backup",
    "func": "main",
    "desc": 'File/dir backup with rotation',
}

if __name__ == '__main__':
    main()
