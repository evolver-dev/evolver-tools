#!/usr/bin/env python3
"""temp-cleaner — Clean temporary files and directories."""
import os
import shutil
import sys
from datetime import datetime, timedelta

TOOL_META = {
    "name": "temp-cleaner",
    "func": "main",
    "desc": "Clean temp files. Usage: temp-cleaner [--dry-run] [--older N[d|h]]",
}

TEMP_DIRS = [
    "/tmp",
    os.path.expanduser("~/.cache"),
    "/var/tmp",
]

def get_size(path):
    total = 0
    try:
        if os.path.isfile(path):
            return os.path.getsize(path)
        for root, dirs, files in os.walk(path):
            for f in files:
                try:
                    total += os.path.getsize(os.path.join(root, f))
                except Exception:
                    pass
    except Exception:
        pass
    return total

def format_size(size):
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

def clean_temp(dry_run, older_seconds):
    cleaned = []
    total_freed = 0
    for temp_dir in TEMP_DIRS:
        if not os.path.isdir(temp_dir):
            continue
        cutoff = datetime.now() - timedelta(seconds=older_seconds) if older_seconds else None
        for entry in os.listdir(temp_dir):
            path = os.path.join(temp_dir, entry)
            try:
                mtime = os.path.getmtime(path)
                if cutoff and datetime.fromtimestamp(mtime) > cutoff:
                    continue
                size = get_size(path)
                if dry_run:
                    cleaned.append((path, size))
                else:
                    if os.path.isfile(path) or os.path.islink(path):
                        os.remove(path)
                    else:
                        shutil.rmtree(path, ignore_errors=True)
                    cleaned.append((path, size))
                total_freed += size
            except Exception:
                pass
    return cleaned, total_freed

def main():
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    older = None
    if "--older" in args:
        idx = args.index("--older")
        if idx + 1 < len(args):
            val = args[idx + 1]
            if val.endswith("d"):
                older = int(val[:-1]) * 86400
            elif val.endswith("h"):
                older = int(val[:-1]) * 3600
            else:
                older = int(val) * 86400  # default to days
    print(f"{'DRY RUN — ' if dry_run else ''}Cleaning temporary files...")
    cleaned, total_freed = clean_temp(dry_run, older)
    if cleaned:
        print(f"Found {len(cleaned)} items ({format_size(total_freed)}):")
        for path, size in cleaned[:30]:
            print(f"  {format_size(size):>8}  {path}")
        if len(cleaned) > 30:
            print(f"  ... and {len(cleaned) - 30} more")
    else:
        print("Nothing to clean.")
    if dry_run and total_freed > 0:
        print(f"\nWould free: {format_size(total_freed)}")
    elif not dry_run and total_freed > 0:
        print(f"\nFreed: {format_size(total_freed)}")

if __name__ == "__main__":
    main()
