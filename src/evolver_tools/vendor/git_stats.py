#!/usr/bin/env python3
"""git-stats — Show git contribution statistics."""
import subprocess
import sys
from collections import defaultdict

TOOL_META = {
    "name": "git-stats",
    "func": "main",
    "desc": "Show git contribution stats. Usage: git-stats [--author name] [--since 30.days]",
}

def main():
    args = sys.argv[1:]
    author = None
    since = None
    i = 0
    while i < len(args):
        if args[i] == "--author" and i + 1 < len(args):
            author = args[i + 1]
            i += 2
        elif args[i] == "--since" and i + 1 < len(args):
            since = args[i + 1]
            i += 2
        else:
            i += 1
    git_cmd = ["git", "log", "--format=%an|%ae|%s", "--no-merges"]
    if author:
        git_cmd.extend(["--author", author])
    if since:
        git_cmd.extend(["--since", since])
    try:
        result = subprocess.run(git_cmd, capture_output=True, text=True, timeout=15)
        if result.returncode != 0:
            print("Not a git repository", file=sys.stderr)
            sys.exit(1)
        commits = result.stdout.strip().split("\n")
        if not commits or commits == [""]:
            print("No commits found")
            return
        author_commits = defaultdict(int)
        author_lines = defaultdict(lambda: {"added": 0, "deleted": 0})
        for commit in commits:
            if "|" not in commit:
                continue
            parts = commit.split("|", 2)
            if len(parts) < 2:
                continue
            name = parts[0].strip()
            author_commits[name] += 1
        # Get detailed stats
        stat_cmd = ["git", "log", "--format=%an|%ae", "--no-merges", "--numstat"]
        if author:
            stat_cmd.extend(["--author", author])
        if since:
            stat_cmd.extend(["--since", since])
        stat_result = subprocess.run(stat_cmd, capture_output=True, text=True, timeout=30)
        if stat_result.returncode == 0:
            current_author = None
            for line in stat_result.stdout.split("\n"):
                if "|" in line:
                    parts = line.split("|", 1)
                    current_author = parts[0].strip()
                elif line.strip() and current_author:
                    parts = line.split("\t")
                    if len(parts) >= 3:
                        try:
                            added = int(parts[0]) if parts[0] != "-" else 0
                            deleted = int(parts[1]) if parts[1] != "-" else 0
                            author_lines[current_author]["added"] += added
                            author_lines[current_author]["deleted"] += deleted
                        except ValueError:
                            pass
        print(f"Git Stats (since: {since or 'beginning'})")
        print("=" * 60)
        print(f"{'Author':<25} {'Commits':>8} {'Added':>8} {'Deleted':>8}")
        print("-" * 60)
        sorted_authors = sorted(author_commits.items(), key=lambda x: -x[1])
        for name, count in sorted_authors:
            added = author_lines[name]["added"] if name in author_lines else 0
            deleted = author_lines[name]["deleted"] if name in author_lines else 0
            print(f"{name:<25} {count:>8} {added:>8} {deleted:>8}")
        total_commits = sum(author_commits.values())
        total_added = sum(a["added"] for a in author_lines.values())
        total_deleted = sum(a["deleted"] for a in author_lines.values())
        print("-" * 60)
        print(f"{'TOTAL':<25} {total_commits:>8} {total_added:>8} {total_deleted:>8}")
    except subprocess.TimeoutExpired:
        print("Command timed out", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
