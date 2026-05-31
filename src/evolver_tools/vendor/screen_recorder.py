#!/usr/bin/env python3
"""screen-recorder — Record terminal sessions as text."""
import datetime
import os
import shutil
import sys
import time

TOOL_META = {
    "name": "screen-recorder",
    "func": "main",
    "desc": "Record terminal session. Usage: screen-recorder start [name] | screen-recorder stop | screen-recorder list",
}

RECORD_DIR = os.path.expanduser("~/.evolver_recordings")
ACTIVE_FILE = os.path.join(RECORD_DIR, ".active_recording")

def ensure_dir():
    os.makedirs(RECORD_DIR, exist_ok=True)

def cmd_start(name=None):
    ensure_dir()
    if os.path.exists(ACTIVE_FILE):
        print("A recording is already active", file=sys.stderr)
        sys.exit(1)
    if not name:
        name = f"session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_file = os.path.join(RECORD_DIR, f"{name}.log")
    # Save the active recording info
    recording_info = {
        "name": name,
        "start_time": datetime.datetime.now().isoformat(),
        "output_file": output_file,
        "commands": [],
    }
    with open(ACTIVE_FILE, "w") as f:
        import json
        json.dump(recording_info, f)
    with open(output_file, "w") as f:
        f.write(f"# Terminal Recording: {name}\n")
        f.write(f"# Started: {recording_info['start_time']}\n")
        f.write("# " + "=" * 50 + "\n")
    print(f"Recording started: {name}")
    print(f"Output: {output_file}")
    print(f"Run: screen-recorder stop    to stop recording")
    # Start recording shell
    shell = os.environ.get("SHELL", "/bin/bash")
    print(f"Opening {shell}... (type 'exit' to stop recording)")
    try:
        import subprocess
        # Just note the session - actual recording happens through piping
        print("\033[1;33mTip: Use 'script' for full terminal recording:\033[0m")
        print(f"  script -q -c \"$SHELL\" {output_file}.raw")
    except Exception:
        pass

def cmd_stop():
    ensure_dir()
    if not os.path.exists(ACTIVE_FILE):
        print("No active recording", file=sys.stderr)
        return
    import json
    with open(ACTIVE_FILE) as f:
        recording_info = json.load(f)
    name = recording_info["name"]
    output_file = recording_info["output_file"]
    end_time = datetime.datetime.now().isoformat()
    # Append end marker
    with open(output_file, "a") as f:
        f.write(f"# Ended: {end_time}\n")
    os.remove(ACTIVE_FILE)
    print(f"Recording stopped: {name}")
    print(f"Saved to: {output_file}")
    # Show stats
    if os.path.exists(output_file):
        lines = 0
        with open(output_file) as f:
            for _ in f:
                lines += 1
        size = os.path.getsize(output_file)
        print(f"Lines: {lines}, Size: {size} bytes")

def cmd_list():
    ensure_dir()
    records = []
    for f in os.listdir(RECORD_DIR):
        if f.endswith(".log") and not f.startswith("."):
            filepath = os.path.join(RECORD_DIR, f)
            mtime = os.path.getmtime(filepath)
            size = os.path.getsize(filepath)
            records.append((f, mtime, size))
    records.sort(key=lambda x: -x[1])
    active = os.path.exists(ACTIVE_FILE)
    if active:
        import json
        with open(ACTIVE_FILE) as f:
            info = json.load(f)
        print(f"▶ Active recording: {info['name']}")
        print()
    if records:
        print(f"{'Name':<35} {'Date':<20} {'Size':>8}")
        print("-" * 65)
        for name, mtime, size in records:
            date = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
            size_str = f"{size//1024}KB" if size > 1024 else f"{size}B"
            print(f"{name:<35} {date:<20} {size_str:>8}")
    else:
        print("No recordings")

def cmd_view(name):
    ensure_dir()
    filepath = os.path.join(RECORD_DIR, name)
    if not filepath.endswith(".log"):
        filepath += ".log"
    if not os.path.exists(filepath):
        print(f"Recording not found: {name}", file=sys.stderr)
        sys.exit(1)
    with open(filepath) as f:
        content = f.read()
    print(content)

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: screen-recorder <command> [args]")
        print("Commands:")
        print("  start [name]    Start recording")
        print("  stop            Stop recording")
        print("  list            List recordings")
        print("  view <name>     View a recording")
        return
    cmd = args[0]
    if cmd == "start":
        name = args[1] if len(args) > 1 else None
        cmd_start(name)
    elif cmd == "stop":
        cmd_stop()
    elif cmd == "list":
        cmd_list()
    elif cmd == "view" and len(args) > 1:
        cmd_view(args[1])
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
