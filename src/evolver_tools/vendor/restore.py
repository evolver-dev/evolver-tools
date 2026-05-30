#!/usr/bin/env python3
"""restore — Restore files/directories from backup archives.

Usage: restore <backup_path> [--dest=<dir>]
       restore backups/myproject.20250101_120000.bak --dest=restored/

Restores .bak backup files or directories created by the 'backup' tool.
Supports dry-run mode to preview what would be restored.
Auto-detects whether source is a file or directory backup.
Zero-dependency (stdlib only).
"""

import sys, os, shutil, glob, datetime

def find_latest_backup(name, backup_dir='.'):
    """Find the most recent backup for a given base name."""
    pattern = os.path.join(backup_dir, f"{name}.*.bak")
    files = sorted(glob.glob(pattern))
    return files[-1] if files else None

def main():
    args = sys.argv[1:]
    if not args or '-h' in args or '--help' in args:
        print(__doc__)
        return

    dest = None
    dry_run = False
    sources = []
    list_backups = False

    for a in args:
        if a.startswith('--dest='):
            dest = a.split('=', 1)[1]
        elif a == '--dry-run':
            dry_run = True
        elif a == '--list':
            list_backups = True
        elif not a.startswith('-'):
            sources.append(a)

    # --list mode: show available backups
    if list_backups:
        backup_dir = sources[0] if sources else '.'
        files = sorted(glob.glob(os.path.join(backup_dir, "*.bak")))
        if not files:
            print(f"  No backup files found in: {backup_dir}")
            return
        print(f"  Available backups in {backup_dir}:")
        print()
        for f in files:
            name = os.path.basename(f)
            size = os.path.getsize(f)
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(f))
            is_dir = os.path.isdir(f)
            kind = "dir " if is_dir else "file"
            print(f"    {name:<45} {size:>8,}B  {mtime:%Y-%m-%d %H:%M}  [{kind}]")
        return

    for src in sources:
        if not os.path.exists(src):
            print(f"  Backup not found: {src}", file=sys.stderr)
            continue

        base = os.path.basename(src)
        # Extract original name: name.timestamp.bak → name
        parts = base.rsplit('.', 2)
        if len(parts) >= 2 and parts[-1] == 'bak':
            orig_name = parts[0]
        else:
            orig_name = base.replace('.bak', '')
        
        if dest:
            restore_target = os.path.join(dest, orig_name)
        else:
            restore_target = orig_name

        if os.path.exists(restore_target) and not dry_run:
            print(f"  Warning: {restore_target} exists. Overwrite? (y/N): ", end='', file=sys.stderr)
            try:
                resp = input().strip().lower()
            except (EOFError, KeyboardInterrupt):
                resp = 'n'
            if resp != 'y':
                print(f"  Skipped: {src}")
                continue

        print(f"  {'[DRY RUN] ' if dry_run else ''}Restoring: {src}")
        print(f"  {'[DRY RUN] ' if dry_run else ''}Target:    {restore_target}")

        if dry_run:
            is_dir = os.path.isdir(src)
            file_type = "directory" if is_dir else "file"
            print(f"  {'[DRY RUN] ' if dry_run else ''}Type:      {file_type}")
            continue

        try:
            if os.path.isdir(src):
                if os.path.exists(restore_target):
                    shutil.rmtree(restore_target)
                shutil.copytree(src, restore_target, symlinks=True)
            else:
                os.makedirs(os.path.dirname(restore_target) or '.', exist_ok=True)
                shutil.copy2(src, restore_target)
            print(f"  Restored: {src} → {restore_target}")
        except Exception as e:
            print(f"  Error: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == '__main__':
    main()
