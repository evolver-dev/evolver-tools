#!/usr/bin/env python3
"""macrogen — Record and replay terminal macro commands."""
import json
import os
import subprocess
import sys
import tempfile
import time

TOOL_META = {
    "name": "macrogen",
    "func": "main",
    "desc": "Record/replay terminal macros. Usage: macrogen record <name> | macrogen replay <name>",
}

MACRO_DIR = os.path.expanduser("~/.evolver_macros")

def ensure_dir():
    os.makedirs(MACRO_DIR, exist_ok=True)

def list_macros():
    if not os.path.isdir(MACRO_DIR):
        return []
    return [f.replace(".json", "") for f in os.listdir(MACRO_DIR) if f.endswith(".json")]

def cmd_record(name):
    ensure_dir()
    path = os.path.join(MACRO_DIR, f"{name}.json")
    if os.path.exists(path):
        print(f"Macro '{name}' already exists. Overwrite? (y/N)", file=sys.stderr)
        resp = input().strip().lower()
        if resp != "y":
            print("Cancelled")
            return
    print(f"Recording macro '{name}'... Press Ctrl+D (or Ctrl+C) when done.")
    print("Enter commands line by line:")
    lines = []
    try:
        while True:
            try:
                line = input()
                lines.append(line)
            except EOFError:
                break
    except KeyboardInterrupt:
        print("\nRecording interrupted")
    macro = {"name": name, "commands": lines, "created": time.time()}
    with open(path, "w") as f:
        json.dump(macro, f, indent=2)
    print(f"Macro '{name}' saved ({len(lines)} commands)")

def cmd_replay(name):
    ensure_dir()
    path = os.path.join(MACRO_DIR, f"{name}.json")
    if not os.path.exists(path):
        print(f"Macro '{name}' not found", file=sys.stderr)
        return
    with open(path) as f:
        macro = json.load(f)
    print(f"Replaying macro '{name}' ({len(macro['commands'])} commands)...")
    for i, cmd in enumerate(macro["commands"], 1):
        print(f"[{i}/{len(macro['commands'])}] $ {cmd}")
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            if result.stdout:
                print(result.stdout.rstrip())
            if result.stderr:
                print(result.stderr.rstrip(), file=sys.stderr)
            if result.returncode != 0:
                print(f"⚠ Command exited with {result.returncode}", file=sys.stderr)
        except subprocess.TimeoutExpired:
            print(f"⚠ Command timed out", file=sys.stderr)
    print(f"Macro '{name}' replay complete")

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: macrogen <command> [args]")
        print("Commands:")
        print("  record <name>   Record a macro")
        print("  replay <name>   Replay a macro")
        print("  list            List saved macros")
        print("  delete <name>   Delete a macro")
        return
    cmd = args[0]
    if cmd == "record" and len(args) > 1:
        cmd_record(args[1])
    elif cmd == "replay" and len(args) > 1:
        cmd_replay(args[1])
    elif cmd == "list":
        macros = list_macros()
        if macros:
            print("Saved macros:")
            for m in macros:
                path = os.path.join(MACRO_DIR, f"{m}.json")
                with open(path) as f:
                    macro = json.load(f)
                print(f"  {m:<20} ({len(macro['commands'])} commands)")
        else:
            print("No macros saved")
    elif cmd == "delete" and len(args) > 1:
        path = os.path.join(MACRO_DIR, f"{args[1]}.json")
        if os.path.exists(path):
            os.remove(path)
            print(f"Macro '{args[1]}' deleted")
        else:
            print(f"Macro '{args[1]}' not found", file=sys.stderr)
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
