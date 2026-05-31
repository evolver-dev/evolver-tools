#!/usr/bin/env python3
"""json-patch — Apply JSON Patch (RFC 6902) operations to JSON files.

Usage:
  json-patch file.json patch.json
  json-patch file.json --add /path value --remove /path
  json-patch file.json --add /name "Alice" --inplace
  json-patch file.json --replace /age 31 --output out.json

Operations (RFC 6902):
  add       Add a value at a JSON Pointer path
  remove    Remove the value at a path
  replace   Replace the value at a path
  move      Move a value from one path to another
  copy      Copy a value from one path to another
  test      Test that a value matches (exits 1 on mismatch)

Zero-dependency (stdlib only).
"""

import sys
import json
import copy


def resolve_pointer(doc, pointer):
    """Resolve a JSON Pointer to (parent, key) in the document.
    Returns (parent_container, key) where container[key] is the target.
    Raises KeyError / IndexError if path does not exist.
    """
    if not pointer.startswith('/'):
        raise ValueError(f"Invalid JSON Pointer: '{pointer}' (must start with '/')")
    if pointer == '/':
        raise ValueError(f"Cannot resolve parent of root in '{pointer}'")
    parts = pointer.strip('/').split('/')
    parts = [_unescape(p) for p in parts]
    current = doc
    for i, part in enumerate(parts[:-1]):
        if isinstance(current, dict):
            if part not in current:
                raise KeyError(f"Path '{'/'.join(parts[:i+1])}' not found")
            current = current[part]
        elif isinstance(current, list):
            idx = int(part) if part.lstrip('-').isdigit() else None
            if idx is None or idx < 0 or idx >= len(current):
                raise IndexError(f"Index '{part}' out of range in list")
            current = current[idx]
        else:
            raise TypeError(f"Cannot traverse into non-container at '{'/'.join(parts[:i+1])}'")
    last_key = parts[-1] if parts else ''
    if isinstance(current, list) and last_key == '-':
        return current, last_key
    return current, last_key


def _unescape(token):
    """Unescape a JSON Pointer token per RFC 6901."""
    token = token.replace('~1', '/')
    token = token.replace('~0', '~')
    return token


def _escape(token):
    """Escape a JSON Pointer token per RFC 6901."""
    token = str(token)
    token = token.replace('~', '~0')
    token = token.replace('/', '~1')
    return token


def resolve_value(doc, pointer):
    """Resolve the value at a JSON Pointer in the document."""
    if pointer == '':
        return doc
    parent, key = resolve_pointer(doc, pointer)
    if isinstance(parent, list) and key == '-':
        raise ValueError("Cannot resolve value at '-' (append sentinel)")
    return parent[key]


def op_add(doc, path, value):
    """Add a value at the given JSON Pointer path."""
    doc = copy.deepcopy(doc)
    if path == '':
        # Replacing root — only valid for test/replace really, but spec allows
        return value
    parent, key = resolve_pointer(doc, path)
    if isinstance(parent, list):
        if key == '-':
            parent.append(value)
        else:
            idx = int(key)
            parent.insert(idx, value)
    elif isinstance(parent, dict):
        parent[key] = value
    return doc


def op_remove(doc, path):
    """Remove the value at the given JSON Pointer path."""
    doc = copy.deepcopy(doc)
    if path == '':
        raise ValueError("Cannot remove root document")
    parent, key = resolve_pointer(doc, path)
    if isinstance(parent, list):
        idx = int(key)
        parent.pop(idx)
    elif isinstance(parent, dict):
        if key not in parent:
            raise KeyError(f"Key '{key}' not found")
        del parent[key]
    return doc


def op_replace(doc, path, value):
    """Replace the value at the given JSON Pointer path."""
    doc = copy.deepcopy(doc)
    if path == '':
        return value
    parent, key = resolve_pointer(doc, path)
    if isinstance(parent, list):
        idx = int(key)
        parent[idx] = value
    elif isinstance(parent, dict):
        parent[key] = value
    return doc


def op_move(doc, from_path, path):
    """Move a value from from_path to path."""
    val = resolve_value(doc, from_path)
    doc = op_remove(doc, from_path)
    doc = op_add(doc, path, val)
    return doc


def op_copy(doc, from_path, path):
    """Copy a value from from_path to path."""
    val = copy.deepcopy(resolve_value(doc, from_path))
    doc = op_add(doc, path, val)
    return doc


def op_test(doc, path, value):
    """Test that the value at path equals the expected value."""
    actual = resolve_value(doc, path)
    if actual != value:
        raise AssertionError(
            f"Test failed at '{path}': expected {json.dumps(value)}, "
            f"got {json.dumps(actual)}"
        )
    return doc


OPERATIONS = {
    'add': op_add,
    'remove': op_remove,
    'replace': op_replace,
    'move': op_move,
    'copy': op_copy,
    'test': op_test,
}


def apply_patch(doc, patch):
    """Apply a list of RFC 6902 patch operations to a document."""
    for op in patch:
        op_type = op.get('op')
        if op_type not in OPERATIONS:
            raise ValueError(f"Unknown operation '{op_type}'")
        path = op.get('path', '')
        if op_type in ('add', 'replace', 'test'):
            value = op.get('value')
            doc = OPERATIONS[op_type](doc, path, value)
        elif op_type == 'remove':
            doc = OPERATIONS[op_type](doc, path)
        elif op_type in ('move', 'copy'):
            from_path = op.get('from', '')
            if not from_path:
                raise ValueError(f"'{op_type}' operation requires 'from' field")
            doc = OPERATIONS[op_type](doc, from_path, path)
    return doc


def parse_cli_ops(args):
    """Parse --add /path value --remove /path etc. into a patch list."""
    patch = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith('--'):
            op_name = arg[2:]
            if op_name not in OPERATIONS:
                raise ValueError(f"Unknown operation '{op_name}'")
            if op_name in ('remove',):
                if i + 1 >= len(args):
                    raise ValueError(f"'{op_name}' requires a path argument")
                patch.append({'op': op_name, 'path': args[i + 1]})
                i += 2
            elif op_name in ('move', 'copy'):
                if i + 3 >= len(args):
                    raise ValueError(f"'{op_name}' requires --from /frompath /topath")
                if args[i + 1] != '--from':
                    raise ValueError(f"'{op_name}' requires --from before source path")
                from_path = args[i + 2]
                target_path = args[i + 3]
                patch.append({'op': op_name, 'from': from_path, 'path': target_path})
                i += 4
            else:
                # add, replace, test
                if i + 2 >= len(args):
                    raise ValueError(f"'{op_name}' requires path and value arguments")
                path_arg = args[i + 1]
                val_str = args[i + 2]
                try:
                    value = json.loads(val_str)
                except json.JSONDecodeError:
                    value = val_str
                patch.append({'op': op_name, 'path': path_arg, 'value': value})
                i += 3
        else:
            i += 1
    return patch


def print_result(data):
    """Print JSON data to stdout."""
    json.dump(data, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write('\n')


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Apply JSON Patch (RFC 6902) operations to JSON files.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            'CLI-style operations:\n'
            '  json-patch file.json --add /name "Alice" --remove /age\n'
            '  json-patch file.json --move --from /old /new\n'
            '\n'
            'Patch file mode:\n'
            '  json-patch file.json patch.json\n'
        ),
    )
    parser.add_argument('file', help='JSON file to patch')
    parser.add_argument('--inplace', action='store_true',
                        help='Modify the file in place')
    parser.add_argument('--output', '-o', metavar='FILE',
                        help='Write result to FILE instead of stdout')

    # Parse known args only — --add/--remove etc are passthrough ops
    parsed, extra = parser.parse_known_args()

    # Read input JSON
    try:
        with open(parsed.file, 'r') as f:
            doc = json.load(f)
    except FileNotFoundError:
        print(f"Error: file not found: {parsed.file}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON in {parsed.file}: {e}", file=sys.stderr)
        sys.exit(1)

    # Determine patch source
    if not extra:
        print("Error: no patch operations provided", file=sys.stderr)
        sys.exit(1)
    elif any(a.startswith('--') for a in extra):
        # CLI-style inline operations
        patch = parse_cli_ops(extra)
    else:
        # First positional arg is patch file
        patch_path = extra[0]
        try:
            with open(patch_path, 'r') as f:
                patch = json.load(f)
        except FileNotFoundError:
            print(f"Error: patch file not found: {patch_path}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: invalid JSON in patch file: {e}", file=sys.stderr)
            sys.exit(1)
        if not isinstance(patch, list):
            print("Error: patch file must contain a JSON array of operations",
                  file=sys.stderr)
            sys.exit(1)

    # Apply the patch
    try:
        result = apply_patch(doc, patch)
    except (ValueError, KeyError, IndexError, TypeError, AssertionError) as e:
        print(f"Error applying patch: {e}", file=sys.stderr)
        sys.exit(1)

    # Output
    if parsed.inplace:
        with open(parsed.file, 'w') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            f.write('\n')
        print(f"Patched {parsed.file} in place", file=sys.stderr)
    elif parsed.output:
        with open(parsed.output, 'w') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            f.write('\n')
    else:
        print_result(result)


TOOL_META = {
    "name": "json-patch",
    "func": "main",
    "desc": "Apply JSON Patch (RFC 6902) operations to JSON files",
}

if __name__ == '__main__':
    main()
