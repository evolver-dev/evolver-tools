#!/usr/bin/env python3
"""git-log-pretty — Pretty git log with graph and formatting."""
import subprocess
import sys

TOOL_META = {
    "name": "git-log-pretty",
    "func": "main",
    "desc": "Pretty git log. Usage: git-log-pretty [--count N] [--author name]",
}

def main():
    args = sys.argv[1:]
    count = 20
    author = None
    i = 0
    while i < len(args):
        if args[i] == "--count" and i + 1 < len(args):
            count = int(args[i + 1])
            i += 2
        elif args[i] == "--author" and i + 1 < len(args):
            author = args[i + 1]
            i += 2
        else:
            i += 1
    # Use pretty git log format
    fmt = "%C(auto)%h%d %C(cyan)%an%Creset %C(green)%ar%Creset%n%s"
    git_cmd = ["git", "log", f"--pretty=format:{fmt}", f"-{count}", "--graph", "--date=relative"]
    if author:
        git_cmd.extend(["--author", author])
    try:
        result = subprocess.run(git_cmd, capture_output=True, text=True, timeout=15)
        if result.returncode != 0:
            print("Not a git repository", file=sys.stderr)
            sys.exit(1)
        output = result.stdout
        if output.strip():
            print(output)
            # Show tag info
            tag_cmd = ["git", "describe", "--tags", "--abbrev=0", "HEAD"]
            tag_result = subprocess.run(tag_cmd, capture_output=True, text=True, timeout=5)
            if tag_result.returncode == 0:
                print(f"\nLatest tag: {tag_result.stdout.strip()}")
        else:
            print("No commits found")
    except subprocess.TimeoutExpired:
        print("Command timed out", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
