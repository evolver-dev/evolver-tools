#!/usr/bin/env python3
"""env-manager — .env file manager. Load, list, get, set, unset, show, diff env files."""
import sys
import os
import argparse
from collections import OrderedDict


def parse_env(content):
    """Parse .env file content into an OrderedDict."""
    env = OrderedDict()
    for line_num, line in enumerate(content.split("\n"), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        # Handle optional export prefix
        cleaned = line
        if cleaned.startswith("export "):
            cleaned = cleaned[7:]
        eq_pos = cleaned.index("=")
        key = cleaned[:eq_pos].strip()
        value = cleaned[eq_pos + 1:].strip()
        # Handle quotes
        if len(value) >= 2:
            if (value[0] == '"' and value[-1] == '"') or (value[0] == "'" and value[-1] == "'"):
                value = value[1:-1]
        env[key] = value
    return env


def serialize_env(env):
    """Serialize OrderedDict back to .env format."""
    lines = []
    for key, value in env.items():
        if " " in value or "#" in value or "=" in value or not value:
            if '"' in value:
                value = "'" + value + "'"
            else:
                value = '"' + value + '"'
        lines.append(f"{key}={value}")
    return "\n".join(lines) + "\n"


def load_env_file(path):
    """Load a .env file, return OrderedDict."""
    if not os.path.isfile(path):
        print(f"Error: File not found: {path}", file=sys.stderr)
        sys.exit(1)
    try:
        with open(path, "r") as f:
            content = f.read()
    except IOError as e:
        print(f"Error reading {path}: {e}", file=sys.stderr)
        sys.exit(1)
    return parse_env(content)


def write_env_file(path, env):
    """Write OrderedDict to .env file."""
    try:
        with open(path, "w") as f:
            f.write(serialize_env(env))
    except IOError as e:
        print(f"Error writing {path}: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_load(args):
    """Load and display a .env file."""
    env = load_env_file(args.file)
    print(serialize_env(env).rstrip())


def cmd_list(args):
    """List all keys in a .env file."""
    env = load_env_file(args.file)
    for key, value in env.items():
        print(f"{key}={value}")


def cmd_get(args):
    """Get a specific key from .env file."""
    env = load_env_file(args.file)
    if args.key in env:
        print(env[args.key])
    else:
        print(f"Key not found: {args.key}", file=sys.stderr)
        sys.exit(1)


def cmd_set(args):
    """Set a key=value in .env file."""
    if "=" not in args.kv:
        print("Error: Use KEY=VALUE format", file=sys.stderr)
        sys.exit(1)
    eq_pos = args.kv.index("=")
    key = args.kv[:eq_pos].strip()
    value = args.kv[eq_pos + 1:].strip()
    if not key:
        print("Error: Key cannot be empty", file=sys.stderr)
        sys.exit(1)
    env = load_env_file(args.file)
    env[key] = value
    write_env_file(args.file, env)
    print(f"Set {key}={value}")


def cmd_unset(args):
    """Unset a key in .env file."""
    env = load_env_file(args.file)
    if args.key in env:
        del env[args.key]
        write_env_file(args.file, env)
        print(f"Unset {args.key}")
    else:
        print(f"Key not found: {args.key}", file=sys.stderr)
        sys.exit(1)


def cmd_show(args):
    """Show .env file content with comments (raw)."""
    if not os.path.isfile(args.file):
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)
    try:
        with open(args.file, "r") as f:
            print(f.read().rstrip())
    except IOError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_diff(args):
    """Diff two .env files."""
    env1 = load_env_file(args.file1)
    env2 = load_env_file(args.file2)

    keys1 = set(env1.keys())
    keys2 = set(env2.keys())

    added = keys2 - keys1
    removed = keys1 - keys2
    common = keys1 & keys2

    changed = {k for k in common if env1[k] != env2[k]}

    has_diff = False

    if added:
        has_diff = True
        print("--- Added keys (in second file only) ---")
        for k in sorted(added):
            print(f"  + {k}={env2[k]}")

    if removed:
        has_diff = True
        print("--- Removed keys (in first file only) ---")
        for k in sorted(removed):
            print(f"  - {k}={env1[k]}")

    if changed:
        has_diff = True
        print("--- Changed keys ---")
        for k in sorted(changed):
            print(f"  ~ {k}:")
            print(f"    - {env1[k]}")
            print(f"    + {env2[k]}")

    if not has_diff:
        print("Files are identical.")
        return

    stats = f"\nSummary: +{len(added)} added, -{len(removed)} removed, ~{len(changed)} changed, ={len(common) - len(changed)} unchanged"
    print(stats)


def main():
    parser = argparse.ArgumentParser(
        description=".env file manager. Load, list, get, set, unset, show, diff."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # load
    p_load = sub.add_parser("load", help="Load and display .env file")
    p_load.add_argument("file", help="Path to .env file")

    # list
    p_list = sub.add_parser("list", help="List all key=value pairs")
    p_list.add_argument("file", help="Path to .env file")

    # get
    p_get = sub.add_parser("get", help="Get a specific key")
    p_get.add_argument("key", help="Key to retrieve")
    p_get.add_argument("file", help="Path to .env file")

    # set
    p_set = sub.add_parser("set", help="Set a key=value")
    p_set.add_argument("kv", help="KEY=VALUE to set")
    p_set.add_argument("file", help="Path to .env file")

    # unset
    p_unset = sub.add_parser("unset", help="Remove a key")
    p_unset.add_argument("key", help="Key to remove")
    p_unset.add_argument("file", help="Path to .env file")

    # show
    p_show = sub.add_parser("show", help="Show raw .env content")
    p_show.add_argument("file", help="Path to .env file")

    # diff
    p_diff = sub.add_parser("diff", help="Diff two .env files")
    p_diff.add_argument("file1", help="First .env file")
    p_diff.add_argument("file2", help="Second .env file")

    args = parser.parse_args()

    try:
        if args.command == "load":
            cmd_load(args)
        elif args.command == "list":
            cmd_list(args)
        elif args.command == "get":
            cmd_get(args)
        elif args.command == "set":
            cmd_set(args)
        elif args.command == "unset":
            cmd_unset(args)
        elif args.command == "show":
            cmd_show(args)
        elif args.command == "diff":
            cmd_diff(args)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)



# === Auto-registration metadata ===
TOOL_META = {
    "name": "env-manager",
    "func": "main",
    "desc": '.env file manager',
}

if __name__ == "__main__":
    main()
