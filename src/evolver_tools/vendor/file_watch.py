#!/usr/bin/env python3
"""file-watch — Watch files/directories for changes (polling)."""
import os, sys, time, json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

TOOL_META = {
    "name": "file-watch",
    "desc": "Watch files/directories for changes (polling)",
    "func": "main",
}

def get_file_state(path):
    """Return state dict for a file."""
    try:
        stat = path.stat()
        return {
            "mtime": stat.st_mtime,
            "size": stat.st_size,
            "mode": stat.st_mode,
        }
    except OSError:
        return None

def format_change(name, old, new):
    """Return a human-readable change string."""
    changes = []
    if old is None and new is not None:
        return f"[NEW]     {name}"
    if old is not None and new is None:
        return f"[DELETED] {name}"
    if old["size"] != new["size"]:
        changes.append(f"size {old['size']}→{new['size']}")
    if old["mtime"] != new["mtime"]:
        dt = datetime.fromtimestamp(new["mtime"]).strftime("%H:%M:%S")
        changes.append(f"modified {dt}")
    if changes:
        return f"[CHANGED] {name} ({', '.join(changes)})"
    return ""

def watch(paths, interval=1.0, recursive=True, events_only=False, once=False):
    """Watch paths for changes."""
    states = {}
    files = []

    for p in paths:
        path = Path(p)
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            pattern = "**/*" if recursive else "*"
            for f in sorted(path.glob(pattern)):
                if f.is_file():
                    files.append(f)

    for f in files:
        state = get_file_state(f)
        if state:
            states[str(f)] = state

    first = True
    while True:
        current_states = {}
        for f in files:
            state = get_file_state(f)
            if state:
                current_states[str(f)] = state

        # Check for changes
        for name in current_states:
            if name not in states:
                msg = format_change(name, None, current_states[name])
                if msg:
                    if events_only:
                        print(json.dumps({"event": "new", "file": name}))
                    else:
                        print(msg)

        for name in list(states.keys()):
            if name not in current_states:
                msg = format_change(name, states[name], None)
                if msg:
                    if events_only:
                        print(json.dumps({"event": "deleted", "file": name}))
                    else:
                        print(msg)

        for name in current_states:
            if name in states:
                msg = format_change(name, states[name], current_states[name])
                if msg:
                    if events_only:
                        print(json.dumps({"event": "changed", "file": name, "old": states[name], "new": current_states[name]}))
                    else:
                        print(msg)

        states = current_states
        if first:
            first = False
            if not events_only:
                print(f"Watching {len(files)} files (interval={interval}s)")

        if once:
            break
        time.sleep(interval)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Watch files for changes")
    parser.add_argument("paths", nargs="+", help="Files or directories to watch")
    parser.add_argument("-i", "--interval", type=float, default=1.0, help="Polling interval (seconds)")
    parser.add_argument("--no-recursive", action="store_true", help="Don't watch subdirectories")
    parser.add_argument("--json", action="store_true", help="JSON event output")
    parser.add_argument("--once", action="store_true", help="Single check (don't keep watching)")
    args = parser.parse_args()

    try:
        watch(args.paths, interval=args.interval, recursive=not args.no_recursive,
              events_only=args.json, once=args.once)
    except KeyboardInterrupt:
        print("\nWatching stopped.")

if __name__ == "__main__":
    main()
