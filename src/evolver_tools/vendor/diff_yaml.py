#!/usr/bin/env python3
"""diff-yaml — Show differences between two YAML files.

Usage: diff-yaml file1.yaml file2.yaml
       diff-yaml file1.yaml file2.yaml --compact
       diff-yaml file1.yaml file2.yaml --context 5
       diff-yaml file1.yaml file2.yaml --output raw

Options:
  --context N        Lines of context around changes (default: 3)
  --compact          Suppress unchanged lines from output
  --output FORMAT    'unified' (default) or 'raw'
"""
import sys
import difflib

try:
    import yaml
except ImportError:
    print(
        "Error: PyYAML is required. Install with: pip install pyyaml",
        file=sys.stderr,
    )
    sys.exit(1)


def flatten(obj, prefix=""):
    """Flatten a nested YAML structure into dot-separated key paths."""
    items = []
    if isinstance(obj, dict):
        for k in sorted(obj.keys()):
            path = f"{prefix}.{k}" if prefix else k
            items.extend(flatten(obj[k], path))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            path = f"{prefix}[{i}]"
            items.extend(flatten(v, path))
    else:
        items.append((prefix, obj))
    return items


def yaml_lines(obj, indent=0):
    """Convert a YAML object to a list of text lines (like yaml.dump but deterministic)."""
    return yaml.dump(obj, default_flow_style=False, sort_keys=True).rstrip("\n").split("\n")


def format_raw_diff(diffs):
    """Format differences in 'raw' style — like json-diff."""
    lines = []
    for path, action, a_val, b_val in diffs:
        lines.append(f"{path}: {action}")
        if a_val is not None:
            lines.append(f"  - {a_val}")
        if b_val is not None:
            lines.append(f"  + {b_val}")
    return lines


def deep_diff(a, b, path=""):
    """Recursively compare two YAML values and yield (path, action, old, new) tuples."""
    if type(a) != type(b):
        yield (path, "type mismatch", type(a).__name__, type(b).__name__)
        return

    if isinstance(a, dict):
        all_keys = set(a) | set(b)
        for k in sorted(all_keys):
            new_path = f"{path}.{k}" if path else k
            if k not in a:
                yield (new_path, "added", None, yaml.dump(b[k], default_flow_style=False).strip())
            elif k not in b:
                yield (new_path, "removed", yaml.dump(a[k], default_flow_style=False).strip(), None)
            else:
                yield from deep_diff(a[k], b[k], new_path)
    elif isinstance(a, list):
        max_len = max(len(a), len(b))
        for i in range(max_len):
            new_path = f"{path}[{i}]"
            if i >= len(a):
                yield (new_path, "added", None, yaml.dump(b[i], default_flow_style=False).strip())
            elif i >= len(b):
                yield (new_path, "removed", yaml.dump(a[i], default_flow_style=False).strip(), None)
            else:
                yield from deep_diff(a[i], b[i], new_path)
    else:
        if a != b:
            yield (path, "changed", repr(a), repr(b))


def main():
    args = sys.argv[1:]

    if "-h" in args or "--help" in args:
        print(__doc__)
        return

    # Parse options
    context = 3
    compact = False
    output_format = "unified"

    filtered = []
    i = 0
    while i < len(args):
        if args[i] == "--context" and i + 1 < len(args):
            context = int(args[i + 1])
            i += 2
        elif args[i] == "--compact":
            compact = True
            i += 1
        elif args[i] == "--output" and i + 1 < len(args):
            output_format = args[i + 1]
            i += 2
        else:
            filtered.append(args[i])
            i += 1

    if len(filtered) != 2:
        print(__doc__)
        sys.exit(1)

    file1, file2 = filtered

    try:
        with open(file1) as f:
            data1 = yaml.safe_load(f)
    except Exception as e:
        print(f"Error reading {file1}: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(file2) as f:
            data2 = yaml.safe_load(f)
    except Exception as e:
        print(f"Error reading {file2}: {e}", file=sys.stderr)
        sys.exit(1)

    # Normalize None to empty string for safe comparison
    if data1 is None and data2 is None:
        print("No differences — files are identical (both empty/null).")
        return
    if data1 is None:
        data1 = ""
    if data2 is None:
        data2 = ""

    if output_format == "raw":
        # Raw format: path-based diffs like json-diff
        diffs = list(deep_diff(data1, data2))
        if diffs:
            print(f"{len(diffs)} difference(s) found:")
            print()
            for line in format_raw_diff(diffs):
                print(line)
        else:
            print("No differences — files are identical.")
        return

    # Unified diff format (default)
    lines1 = yaml_lines(data1)
    lines2 = yaml_lines(data2)

    # Add trailing newlines so context shows blank lines properly
    lines1.append("")
    lines2.append("")

    if compact:
        # Compact mode: only show changed line numbers and their values
        diff_gen = difflib.Differ().compare(lines1, lines2)
        changes = [l for l in diff_gen if l.startswith("+ ") or l.startswith("- ")]
        if changes:
            for l in changes:
                print(l)
        else:
            print("No differences — files are identical.")
        return

    # Standard unified diff with context
    diff_lines = list(
        difflib.unified_diff(
            lines1,
            lines2,
            fromfile=file1,
            tofile=file2,
            n=context,
        )
    )
    if diff_lines:
        sys.stdout.write("\n".join(diff_lines) + "\n")
    else:
        print("No differences — files are identical.")


TOOL_META = {
    "name": "diff-yaml",
    "func": "main",
    "desc": "Show differences between two YAML files",
}

if __name__ == "__main__":
    main()
