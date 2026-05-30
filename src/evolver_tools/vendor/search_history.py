#!/usr/bin/env python3
"""search-history — Search terminal history."""
import os
import sys

TOOL_META = {
    "name": "search-history",
    "func": "main",
    "desc": "Search terminal history. Usage: search-history <pattern>",
}

HISTORY_FILES = [
    os.path.expanduser("~/.bash_history"),
    os.path.expanduser("~/.zsh_history"),
    os.path.expanduser("~/.history"),
]

def find_history_files():
    files = []
    for f in HISTORY_FILES:
        if os.path.exists(f):
            files.append(f)
    # Try to find more
    home = os.path.expanduser("~")
    for root, dirs, fnames in os.walk(home):
        for fn in fnames:
            if fn in (".bash_history", ".zsh_history", ".history", ".fish_history"):
                fp = os.path.join(root, fn)
                if fp not in files:
                    files.append(fp)
        if len(files) > 5:
            break
    return files

def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: search-history <pattern>", file=sys.stderr)
        print("       search-history <pattern> --max N", file=sys.stderr)
        sys.exit(1)
    pattern = args[0]
    max_results = 50
    if "--max" in args:
        idx = args.index("--max")
        if idx + 1 < len(args):
            max_results = int(args[idx + 1])
    history_files = find_history_files()
    if not history_files:
        print("No history files found", file=sys.stderr)
        sys.exit(1)
    results = []
    for hf in history_files:
        try:
            with open(hf, "r", errors="ignore") as f:
                for line in f:
                    line = line.rstrip("\n")
                    if line.startswith(":"):
                        line = line.split(";", 1)[-1] if ";" in line else line
                    if pattern.lower() in line.lower():
                        results.append(line)
        except Exception:
            pass
    if not results:
        print(f"No matches for: {pattern}")
        return
    # Deduplicate
    seen = set()
    unique = []
    for r in results:
        if r not in seen:
            seen.add(r)
            unique.append(r)
    for r in unique[:max_results]:
        print(r)
    if len(unique) > max_results:
        print(f"... and {len(unique) - max_results} more")

if __name__ == "__main__":
    main()
