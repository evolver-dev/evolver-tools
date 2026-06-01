#!/usr/bin/env python3
"""git-branch-cleaner — Clean stale git branches. List merged, stale, orphaned branches."""
import sys
import os
import argparse
import subprocess
from datetime import datetime, timedelta


def run_git(args):
    """Run git command and return stdout. Exit on error."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )
        if result.returncode != 0:
            print(f"Git error: {result.stderr.strip()}", file=sys.stderr)
            sys.exit(1)
        return result.stdout.strip()
    except FileNotFoundError:
        print("Error: git not found. Is git installed?", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"Error running git: {e}", file=sys.stderr)
        sys.exit(1)


def get_current_branch():
    """Get the current branch name."""
    return run_git(["rev-parse", "--abbrev-ref", "HEAD"])


def list_merged_branches(include_current=False):
    """List branches merged into the current branch."""
    current = get_current_branch()
    merged = run_git(["branch", "--merged"]).split("\n")
    branches = [b.strip().lstrip("* ").strip() for b in merged if b.strip()]
    if not include_current:
        branches = [b for b in branches if b != current]
    return branches


def list_branches_without_remote():
    """List local branches that have no remote tracking branch."""
    branches = run_git(["branch", "-vv"]).split("\n")
    orphans = []
    for line in branches:
        line = line.strip().lstrip("* ").strip()
        if not line:
            continue
        parts = line.split()
        branch_name = parts[0]
        # Branches without remote tracking show as `branch_name ` or `branch_name [gone]`
        if len(parts) < 3 or "[gone]" in line:
            if "[gone]" in line or not line.split(None, 2)[1].startswith("["):
                orphans.append(branch_name)
        else:
            # Check if it has a remote tracking branch
            tracking = parts[1] if len(parts) > 1 else ""
            if not tracking.startswith("["):
                orphans.append(branch_name)
    # Filter out the current branch
    current = get_current_branch()
    current_full_line = [l for l in run_git(["branch"]).split("\n") if l.strip().startswith("*")]
    if current_full_line:
        parts = current_full_line[0].strip().lstrip("* ").split()
        current = parts[0] if parts else current
    return [b for b in orphans if b != current]


def list_branches_older_than(days):
    """List branches older than N days based on commit date."""
    current = get_current_branch()
    branches = run_git(["branch"]).split("\n")
    old_branches = []
    cutoff = datetime.now() - timedelta(days=days)

    for line in branches:
        branch = line.strip().lstrip("* ").strip()
        if not branch or branch == current:
            continue
        try:
            date_str = run_git(["log", "-1", "--format=%ci", branch])
            if not date_str:
                continue
            commit_date = datetime.strptime(date_str.strip(), "%Y-%m-%d %H:%M:%S %z")
            # Make naive for comparison
            commit_date_naive = commit_date.replace(tzinfo=None)
            if commit_date_naive < cutoff:
                days_old = (datetime.now() - commit_date_naive).days
                old_branches.append((branch, commit_date_naive.strftime("%Y-%m-%d"), days_old))
        except (subprocess.CalledProcessError, ValueError) as e:
            # Skip branches we can't process
            pass
    return old_branches


def delete_branches(branches, force=False):
    """Delete branches safely."""
    if not branches:
        print("No branches to delete.")
        return

    print(f"\nThe following branches will be deleted:")
    for b in branches:
        print(f"  - {b}")

    if not force:
        try:
            response = input("\nConfirm deletion? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            return
        if response not in ("y", "yes"):
            print("Aborted.")
            return

    deleted = 0
    failed = 0
    for branch in branches:
        try:
            run_git(["branch", "-d", branch])
            print(f"  Deleted: {branch}")
            deleted += 1
        except SystemExit:
            print(f"  Failed to delete: {branch} (may not be fully merged)", file=sys.stderr)
            failed += 1

    print(f"\nResult: {deleted} deleted, {failed} failed")


def cmd_merged(args):
    """List and optionally clean merged branches."""
    branches = list_merged_branches()
    if not branches:
        print("No merged branches found.")
        return

    print(f"Merged branches ({len(branches)}):")
    for b in branches:
        print(f"  {b}")

    if args.clean_merged:
        delete_branches(branches, force=args.force)


def cmd_stale(args):
    """List branches older than N days."""
    days = args.days
    old_branches = list_branches_older_than(days)
    if not old_branches:
        print(f"No branches older than {days} days.")
        return

    print(f"Branches older than {days} days ({len(old_branches)}):")
    for name, date, days_old in sorted(old_branches, key=lambda x: x[2], reverse=True):
        print(f"  {name:<30} last commit: {date} ({days_old} days old)")


def cmd_orphan(args):
    """List branches without remote tracking."""
    orphans = list_branches_without_remote()
    if not orphans:
        print("No orphan branches found.")
        return

    print(f"Orphan branches (no remote tracking) ({len(orphans)}):")
    for b in orphans:
        print(f"  {b}")

    if args.delete and args.force:
        delete_branches(orphans, force=True)
    elif args.delete:
        delete_branches(orphans, force=False)


def cmd_clean_all(args):
    """Delete all merged branches."""
    branches = list_merged_branches()
    if not branches:
        print("No merged branches to clean.")
        return
    delete_branches(branches, force=args.force)


def main():
    parser = argparse.ArgumentParser(
        description="Clean stale git branches. List and delete merged, stale, orphan branches."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # merged
    p_merged = sub.add_parser("merged", help="List branches merged into current branch")
    p_merged.add_argument("--clean-merged", action="store_true", help="Delete merged branches")
    p_merged.add_argument("--force", "-f", action="store_true", help="Skip confirmation")

    # stale
    p_stale = sub.add_parser("stale", help="List branches older than N days")
    p_stale.add_argument("days", type=int, help="Age in days")
    p_stale.add_argument("--delete", action="store_true", help="Delete stale branches")
    p_stale.add_argument("--force", "-f", action="store_true", help="Skip confirmation")

    # orphan
    p_orphan = sub.add_parser("orphan", help="List branches without remote tracking")
    p_orphan.add_argument("--delete", action="store_true", help="Delete orphan branches")
    p_orphan.add_argument("--force", "-f", action="store_true", help="Skip confirmation")

    # clean-merged
    p_clean = sub.add_parser("clean-merged", help="Delete all merged branches")
    p_clean.add_argument("--force", "-f", action="store_true", help="Skip confirmation")

    args = parser.parse_args()

    try:
        if args.command == "merged":
            cmd_merged(args)
        elif args.command == "stale":
            cmd_stale(args)
        elif args.command == "orphan":
            cmd_orphan(args)
        elif args.command == "clean-merged":
            cmd_clean_all(args)
    except KeyboardInterrupt:
        print("\nInterrupted.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)



# === Auto-registration metadata ===
TOOL_META = {
    "name": "git-branch-cleaner",
    "func": "main",
    "desc": 'Clean stale git branches',
}

if __name__ == "__main__":
    main()
