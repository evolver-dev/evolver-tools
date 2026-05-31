#!/usr/bin/env python3
"""json-keys — Extract and list keys from JSON files.

Usage: json-keys data.json
       cat data.json | json-keys
       json-keys data.json --depth 2 --path items
       json-keys data.json --flatten
       json-keys data.json --values --max 20
"""

import sys
import json
import argparse
from pathlib import Path


def extract_keys(data, path_prefix="", depth=-1, current_depth=0, flatten=False):
    """Recursively extract keys from JSON data."""
    keys = set()

    if depth != -1 and current_depth > depth:
        return keys

    if isinstance(data, dict):
        for key, value in data.items():
            full_key = f"{path_prefix}.{key}" if path_prefix else key
            if flatten:
                keys.add(full_key)
                keys.update(extract_keys(value, full_key, depth, current_depth + 1, flatten))
            else:
                keys.add(key)
                keys.update(extract_keys(value, path_prefix, depth, current_depth + 1, flatten))
    elif isinstance(data, list):
        for item in data:
            keys.update(extract_keys(item, path_prefix, depth, current_depth + 1, flatten))

    return keys


def get_value_at_path(data, path_parts):
    """Navigate JSON data following a list of path keys."""
    current = data
    for part in path_parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif isinstance(current, list):
            try:
                idx = int(part)
                current = current[idx]
            except (ValueError, IndexError):
                return None
        else:
            return None
    return current


def collect_values(data, path_parts, path_prefix="", depth=-1, current_depth=0, max_values=10):
    """Collect sample values for each key in the data."""
    samples = {}

    if depth != -1 and current_depth > depth:
        return samples

    if isinstance(data, dict):
        for key, value in data.items():
            full_path = f"{path_prefix}.{key}" if path_prefix else key
            full_path_parts = path_parts + [key]

            # Collect a sample value (first encountered)
            if full_path not in samples and not isinstance(value, (dict, list)):
                samples[full_path] = str(value)[:80]

            # Recurse
            deeper = collect_values(value, full_path_parts, full_path, depth, current_depth + 1, max_values)
            for k, v in deeper.items():
                if k not in samples and len(samples) < max_values:
                    samples[k] = v
    elif isinstance(data, list):
        for item in data[:5]:  # Limit to first 5 list items for sampling
            deeper = collect_values(item, path_parts, path_prefix, depth, current_depth + 1, max_values)
            for k, v in deeper.items():
                if k not in samples and len(samples) < max_values:
                    samples[k] = v

    return samples


def main():
    parser = argparse.ArgumentParser(
        description="Extract and list keys from JSON files.",
        add_help=False,
    )
    parser.add_argument("file", nargs="?", help="JSON file to read (reads stdin if omitted)")
    parser.add_argument("--depth", "-d", type=int, default=1, help="How deep to recurse (default: 1, -1 for infinite)")
    parser.add_argument("--path", "-p", default="", help="Only show keys under this JSON path")
    parser.add_argument("--values", "-v", action="store_true", help="Show sample values for each key")
    parser.add_argument("--flatten", "-f", action="store_true", help="Flatten nested keys with dot notation")
    parser.add_argument("--max", "-m", type=int, default=10, help="Max sample values to show (default: 10)")

    # Parse with custom handling for -h/--help
    argv = sys.argv[1:]
    if "-h" in argv or "--help" in argv:
        print(__doc__)
        sys.exit(0)

    args = parser.parse_args(argv)

    # Read JSON data
    try:
        if args.file:
            with open(args.file, "r") as f:
                data = json.load(f)
        else:
            if sys.stdin.isatty():
                print("Error: No input provided. Use a file argument or pipe JSON via stdin.", file=sys.stderr)
                sys.exit(1)
            data = json.load(sys.stdin)
    except FileNotFoundError as e:
        print(f"Error: File not found: {e.filename}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Navigate to sub-path if requested
    if args.path:
        path_parts = [p for p in args.path.split(".") if p]
        data = get_value_at_path(data, path_parts)
        if data is None:
            print(f"Error: Path '{args.path}' not found in JSON data.", file=sys.stderr)
            sys.exit(1)

    # Extract and display keys
    depth = args.depth
    if args.values:
        samples = collect_values(data, [], "", depth, 0, args.max)
        if not samples:
            print("(no keys with scalar values found)")
        else:
            max_key_len = max(len(k) for k in samples)
            for key, value in samples.items():
                print(f"{key:<{max_key_len + 2}} {value}")
    else:
        keys = extract_keys(data, "", depth, 0, args.flatten)
        if not keys:
            print("(no keys found)")
        else:
            sorted_keys = sorted(keys)
            for k in sorted_keys:
                print(k)


TOOL_META = {"name": "json-keys", "func": "main", "desc": "Extract and list keys from JSON files"}


if __name__ == "__main__":
    main()
