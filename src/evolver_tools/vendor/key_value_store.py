#!/usr/bin/env python3
"""key-value-store — Simple CLI key-value store."""
import json
import os
import sys

TOOL_META = {
    "name": "key-value-store",
    "func": "main",
    "desc": "Simple key-value store. Usage: kvstore set <key> <val> | kvstore get <key> | kvstore list | kvstore del <key>",
}

STORE_PATH = os.path.expanduser("~/.evolver_kvstore.json")

def load_store():
    if os.path.exists(STORE_PATH):
        try:
            with open(STORE_PATH) as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_store(data):
    with open(STORE_PATH, "w") as f:
        json.dump(data, f, indent=2)

def cmd_set(key, value):
    data = load_store()
    data[key] = value
    save_store(data)
    print(f"✓ Set: {key} = {value}")

def cmd_get(key):
    data = load_store()
    if key in data:
        print(data[key])
    else:
        print(f"Key not found: {key}", file=sys.stderr)
        sys.exit(1)

def cmd_list():
    data = load_store()
    if data:
        for key, val in data.items():
            val_str = str(val)[:60]
            print(f"  {key:<20} = {val_str}")
        print(f"\nTotal: {len(data)} keys")
    else:
        print("Empty store")

def cmd_delete(key):
    data = load_store()
    if key in data:
        del data[key]
        save_store(data)
        print(f"✓ Deleted: {key}")
    else:
        print(f"Key not found: {key}", file=sys.stderr)
        sys.exit(1)

def cmd_search(pattern):
    data = load_store()
    results = [(k, v) for k, v in data.items() if pattern.lower() in k.lower()]
    if results:
        for key, val in results:
            print(f"  {key:<20} = {val}")
        print(f"\nFound: {len(results)} keys")
    else:
        print(f"No keys matching: {pattern}")

def cmd_export(filepath):
    data = load_store()
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Exported {len(data)} keys to {filepath}")

def cmd_import(filepath):
    with open(filepath) as f:
        imported = json.load(f)
    data = load_store()
    data.update(imported)
    save_store(data)
    print(f"Imported {len(imported)} keys")

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: kvstore <command> [args]")
        print("Commands:")
        print("  set <key> <value>    Store a value")
        print("  get <key>            Retrieve a value")
        print("  list                 List all keys")
        print("  del <key>            Delete a key")
        print("  search <pattern>     Search keys")
        print("  export <file>        Export all data")
        print("  import <file>        Import data")
        return
    cmd = args[0]
    try:
        if cmd == "set" and len(args) >= 3:
            cmd_set(args[1], " ".join(args[2:]))
        elif cmd == "get" and len(args) >= 2:
            cmd_get(args[1])
        elif cmd == "list":
            cmd_list()
        elif cmd == "del" and len(args) >= 2:
            cmd_delete(args[1])
        elif cmd == "search" and len(args) >= 2:
            cmd_search(args[1])
        elif cmd == "export" and len(args) >= 2:
            cmd_export(args[1])
        elif cmd == "import" and len(args) >= 2:
            cmd_import(args[1])
        else:
            print(f"Unknown command or missing args", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
