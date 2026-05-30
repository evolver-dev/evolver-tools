#!/usr/bin/env python3
"""search-history — Search shell command history (bash/zsh/fish)."""
import os, sys, re, json, gzip
from pathlib import Path
from collections import Counter

TOOL_META = {
    "name": "search-history",
    "desc": "Search shell command history (bash, zsh, fish)",
    "func": "main",
}

HISTORY_PATHS = {
    "bash": "~/.bash_history",
    "zsh": "~/.zsh_history",
    "fish": "~/.local/share/fish/fish_history",
    "lesshst": "~/.lesshst",
}

def read_bash_history(path):
    """Read bash history format (one command per line, optionally prefixed with #timestamp)."""
    entries = []
    ts = ""
    with open(path, "r", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n\r")
            if line.startswith("#"):
                try:
                    ts = int(line[1:])
                except ValueError:
                    ts = line[1:]
            elif line:
                entries.append({"cmd": line, "ts": ts, "source": "bash"})
                ts = ""
    return entries

def read_zsh_history(path):
    """Read zsh history format (: <ts>:<n>;<command>)."""
    entries = []
    pat = re.compile(r"^:\s*(\d+):\d+;(.+)$")
    with open(path, "r", errors="replace") as f:
        for line in f:
            m = pat.match(line.rstrip())
            if m:
                entries.append({"cmd": m.group(2), "ts": int(m.group(1)), "source": "zsh"})
    return entries

def read_fish_history(path):
    """Read fish history format (- cmd: <cmd>\n   when: <ts>)."""
    entries = []
    current = {}
    with open(path, "r", errors="replace") as f:
        for line in f:
            line = line.rstrip()
            if line.startswith("- cmd:"):
                if current:
                    entries.append(current)
                current = {"cmd": line[6:].strip(), "ts": "", "source": "fish"}
            elif line.startswith("  when:") and current:
                current["ts"] = line[7:].strip()
        if current:
            entries.append(current)
    return entries

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Search shell command history")
    parser.add_argument("pattern", nargs="?", default="", help="Search pattern (regex)")
    parser.add_argument("-s", "--shell", choices=["bash", "zsh", "fish", "all"], default="all", help="Shell history to search")
    parser.add_argument("-n", "--count", type=int, default=20, help="Max results")
    parser.add_argument("-r", "--rank", action="store_true", help="Rank by frequency")
    parser.add_argument("-p", "--popular", action="store_true", help="Show most used commands")
    parser.add_argument("--stats", action="store_true", help="Show history stats")
    args = parser.parse_args()

    shells = ["bash", "zsh", "fish"] if args.shell == "all" else [args.shell]
    readers = {"bash": read_bash_history, "zsh": read_zsh_history, "fish": read_fish_history}

    all_entries = []
    for shell in shells:
        path = os.path.expanduser(HISTORY_PATHS[shell])
        if not os.path.exists(path):
            continue
        try:
            all_entries.extend(readers[shell](path))
        except Exception as e:
            print(f"Warning: cannot read {path}: {e}", file=sys.stderr)

    if not all_entries:
        print("No history files found.")
        return

    if args.stats:
        total = len(all_entries)
        uniq = len(set(e["cmd"] for e in all_entries))
        cmd_counter = Counter(e["cmd"].split()[0] if e["cmd"].split() else "" for e in all_entries)
        top_cmds = cmd_counter.most_common(10)
        print(f"Total commands: {total}")
        print(f"Unique commands: {uniq}")
        print(f"Shell sources: {', '.join(shells)}")
        print(f"\nTop commands:")
        for cmd, cnt in top_cmds:
            bar = "█" * min(cnt, 40)
            print(f"  {cmd:15s} {cnt:5d} {bar}")
        return

    if args.popular:
        cmd_counter = Counter(e["cmd"] for e in all_entries)
        for cmd, cnt in cmd_counter.most_common(args.count):
            bar = "█" * min(cnt, 40)
            print(f"  {cnt:4d}x {cmd}")
            print(f"       {bar}")
        return

    if not args.pattern:
        parser.print_help()
        return

    try:
        pat = re.compile(args.pattern, re.IGNORECASE)
    except re.error as e:
        print(f"Invalid regex: {e}")
        sys.exit(1)

    matches = [e for e in all_entries if pat.search(e["cmd"])]
    matches = matches[-args.count:] if args.rank else matches[:args.count]

    if not matches:
        print(f"No matches for: {args.pattern}")
        return

    for e in reversed(matches):
        ts_str = f"[{e['ts']}] " if e['ts'] else ""
        print(f"  {ts_str}{e['cmd']}")

    print(f"\n({len(matches)} matches)")

if __name__ == "__main__":
    main()
