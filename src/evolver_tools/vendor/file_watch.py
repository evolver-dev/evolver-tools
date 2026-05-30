#!/usr/bin/env python3
"""file-watch — Watch a file for changes in real-time."""
import os
import sys
import time
from datetime import datetime

TOOL_META = {
    "name": "file-watch",
    "func": "main",
    "desc": "Watch file for changes. Usage: file-watch <file> [--tail]",
}

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: file-watch <file> [--tail]", file=sys.stderr)
        print("  --tail  Follow new content (like tail -f)", file=sys.stderr)
        sys.exit(1)
    filepath = args[0]
    follow = "--tail" in args
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    last_mtime = os.path.getmtime(filepath)
    last_size = os.path.getsize(filepath)
    if follow:
        # Read existing content first
        try:
            with open(filepath, "r") as f:
                content = f.read()
            print(content, end="")
        except Exception:
            pass
        print(f"\n[ Watching {filepath} for changes — Ctrl+C to stop ]")
        try:
            while True:
                time.sleep(0.5)
                if os.path.getmtime(filepath) != last_mtime:
                    new_size = os.path.getsize(filepath)
                    if new_size > last_size:
                        with open(filepath, "r") as f:
                            f.seek(last_size)
                            new_data = f.read()
                        print(new_data, end="", flush=True)
                    else:
                        # File was truncated or rewritten
                        with open(filepath, "r") as f:
                            print(f"\n--- File updated at {datetime.now().strftime('%H:%M:%S')} ---")
                            print(f.read(), end="", flush=True)
                    last_mtime = os.path.getmtime(filepath)
                    last_size = new_size
        except KeyboardInterrupt:
            print("\n[ Stopped ]")
    else:
        print(f"Last modified: {datetime.fromtimestamp(last_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Size: {last_size} bytes")
        print("---")
        try:
            with open(filepath, "r") as f:
                print(f.read())
        except Exception as e:
            print(f"Error reading: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
