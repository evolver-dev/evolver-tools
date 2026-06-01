#!/usr/bin/env python3
"""json-path — Query JSON with simple path syntax.

Usage:
  json-path file.json --path=users.0.name
  cat file.json | json-path --path=users[0].name
  json-path file.json --path=users[*].id
  json-path file.json --path='users.*.name'

Supports dot notation (key), bracket notation ([0], ['key']),
numeric indices (0), and wildcards ([*] or .*) for iterating
over all items in a list or values in a dict.

Zero-dependency (stdlib only).
"""

import sys
import json
import re


def tokenize_path(path):
    """Split a path string into a list of token tuples.

    Each token is one of:
      ('key', str)     — dict key or initial identifier
      ('index', int)   — numeric list index
      ('wildcard',)    — wildcard expansion [*] or .*
    """
    tokens = []
    i = 0
    path = path.strip()
    n = len(path)

    # Leading identifier (first token, no leading dot)
    # e.g. "users.0.name" starts with "users"
    if n > 0 and (path[i].isalpha() or path[i] == '_'):
        m = re.match(r'\w+', path[i:])
        if m:
            tokens.append(('key', m.group(0)))
            i += m.end()

    while i < n:
        ch = path[i]

        if ch == '.':
            i += 1
            if i >= n:
                raise ValueError(f"Unexpected end of path after '.' at position {i}")
            # Dot-wildcard .*
            if path[i] == '*':
                tokens.append(('wildcard',))
                i += 1
            else:
                m = re.match(r'\w+', path[i:])
                if m:
                    tokens.append(('key', m.group(0)))
                    i += m.end()
                else:
                    raise ValueError(
                        f"Invalid token after '.' at position {i}: "
                        f"expected identifier or '*'"
                    )

        elif ch == '[':
            i += 1
            if i >= n:
                raise ValueError(f"Unterminated '[' at position {i - 1}")
            # Bracket wildcard [*]
            if path[i] == '*':
                tokens.append(('wildcard',))
                i += 1
            # Bracket numeric index [0], [42]
            elif path[i].isdigit():
                m = re.match(r'\d+', path[i:])
                tokens.append(('index', int(m.group(0))))
                i += m.end()
            # Bracket quoted key ['key'] or ["key"]
            elif path[i] in ("'", '"'):
                quote = path[i]
                i += 1
                end = path.find(quote, i)
                if end == -1:
                    raise ValueError(
                        f"Unterminated string in brackets starting at position {i}"
                    )
                tokens.append(('key', path[i:end]))
                i = end + 1
            else:
                raise ValueError(
                    f"Invalid content inside brackets at position {i}: "
                    f"expected number, '*', or quoted string"
                )
            # Expect closing bracket
            if i >= n or path[i] != ']':
                raise ValueError(f"Expected ']' at position {i}")
            i += 1

        else:
            raise ValueError(
                f"Unexpected character {ch!r} at position {i} "
                f"in path {path!r}"
            )

    return tokens


def _walk(data, tokens):
    """Walk tokens against data, yielding (value, display_path) tuples.

    Handles wildcards by expanding into multiple branches.
    """
    # Each entry: (current_value, path_so_far)
    stack = [(data, '$')]

    for token in tokens:
        next_stack = []
        for value, cur_path in stack:
            if value is None:
                continue

            typ = token[0]

            if typ == 'key':
                key = token[1]
                # If value is a dict, try dictionary lookup
                if isinstance(value, dict):
                    if key in value:
                        next_stack.append((value[key], f'{cur_path}.{key}'))
                # If value is a list and key is all-digits, try numeric index
                elif isinstance(value, list) and key.isdigit():
                    idx = int(key)
                    if 0 <= idx < len(value):
                        next_stack.append((value[idx], f'{cur_path}[{idx}]'))
                # Try dict-style access on non-dict (will fail, skip)
                # Just skip unresolvable keys silently

            elif typ == 'index':
                idx = token[1]
                if isinstance(value, list):
                    if 0 <= idx < len(value):
                        next_stack.append((value[idx], f'{cur_path}[{idx}]'))
                elif isinstance(value, dict):
                    # Allow integer-keyed dicts
                    if str(idx) in value:
                        next_stack.append((value[str(idx)], f'{cur_path}.{str(idx)}'))

            elif typ == 'wildcard':
                if isinstance(value, list):
                    for i, item in enumerate(value):
                        next_stack.append((item, f'{cur_path}[{i}]'))
                elif isinstance(value, dict):
                    for k, v in value.items():
                        next_stack.append((v, f'{cur_path}.{k}'))
                # Wildcard on scalar yields nothing (no expansion)

        stack = next_stack
        if not stack:
            break

    return stack


def resolve_path(data, path):
    """Resolve a path like 'users.0.name' or 'users[*].id' against data.

    Returns a list of (value, display_path) tuples.
    Wildcards produce multiple results; literal paths produce one.
    Returns empty list if nothing matched.
    """
    tokens = tokenize_path(path)
    return _walk(data, tokens)


def read_json(source_path=None):
    """Read JSON from a file or stdin."""
    if source_path:
        with open(source_path) as f:
            return json.load(f)
    else:
        return json.load(sys.stdin)


def main():
    args = sys.argv[1:]

    if '-h' in args or '--help' in args:
        print(__doc__.strip())
        return

    # Extract --path= argument
    path_str = None
    file_args = []
    for a in args:
        if a.startswith('--path='):
            path_str = a[len('--path='):]
        elif a == '--path' or a == '-p':
            # Next arg will be consumed below
            continue
        else:
            file_args.append(a)

    # Handle -p <path> or --path <path> (consuming next arg)
    for i, a in enumerate(args):
        if a in ('--path', '-p') and i + 1 < len(args):
            path_str = args[i + 1]
            break

    if not path_str:
        print("Usage: json-path [file] --path=<path>", file=sys.stderr)
        print("       cat file.json | json-path --path=<path>", file=sys.stderr)
        print("Use -h for full help.", file=sys.stderr)
        sys.exit(1)

    # Determine source: file arg or stdin
    source_path = None
    for a in file_args:
        if a != path_str and not a.startswith('-'):
            source_path = a
            break

    try:
        data = read_json(source_path)
    except FileNotFoundError:
        print(f"Error: file not found: {source_path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON — {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading input: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        results = resolve_path(data, path_str)
    except ValueError as e:
        print(f"Error in path: {e}", file=sys.stderr)
        sys.exit(1)

    if not results:
        print(f"No results for path: {path_str}", file=sys.stderr)
        sys.exit(1)

    # Single match → print just the value
    if len(results) == 1:
        val, _ = results[0]
        print(json.dumps(val, indent=2, ensure_ascii=False))
    else:
        # Multiple matches → print as array with path annotations
        output = [{'path': p, 'value': v} for v, p in results]
        print(json.dumps(output, indent=2, ensure_ascii=False))


TOOL_META = {
    "name": "json-path",
    "func": "main",
    "desc": "Query JSON with simple path syntax — dot notation, bracket, wildcard",
}

if __name__ == '__main__':
    main()
