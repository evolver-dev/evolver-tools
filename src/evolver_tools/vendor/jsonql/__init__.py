"""
jsonql — Zero-dependency JSON query tool for CLI.

Supports:
  - Read from file or stdin
  - Path queries: $.key.subkey, $.arr[0], $.arr[*].field
  - Filter: $[?(@.key > 5)]
  - Output: pretty, compact, raw (plain text extraction)
"""

import json
import os
import re
import sys
import argparse
from typing import Any, Callable, Optional


# ---------- query parsing ----------

def _tokenize(path: str) -> list:
    """Tokenize a JSON path expression into tokens."""
    tokens = []
    i = 0
    # strip leading $. or $
    if path.startswith('$.'):
        path = path[2:]
    elif path.startswith('$'):
        path = path[1:]

    while i < len(path):
        c = path[i]
        if c == '.':
            i += 1  # skip dot separator
        elif c == '[':
            # bracket expression: [0], [*], [?(@.key op value)]
            end = path.index(']', i)
            expr = path[i+1:end]
            i = end + 1
            if expr == '*':
                tokens.append(('wildcard',))
            elif expr.startswith('?(') and expr.endswith(')'):
                tokens.append(('filter', expr[2:-1]))
            else:
                try:
                    tokens.append(('index', int(expr)))
                except ValueError:
                    tokens.append(('key', expr.strip("'\"")))
        elif c == '*' and (i + 1 >= len(path) or path[i+1] in ('.', '[') or i+1 == len(path)):
            tokens.append(('wildcard',))
            i += 1
        else:
            # dot-key
            j = i
            while j < len(path) and path[j] not in ('.', '['):
                j += 1
            key = path[i:j]
            if key == '*':
                tokens.append(('wildcard',))
            else:
                tokens.append(('key', key))
            i = j
    return tokens


def _compile_filter(expr: str) -> Callable[[Any], bool]:
    """Compile a filter expression like '@.age > 25' into a callable."""
    expr = expr.strip()
    # Match: @.path OPERATOR value
    # Operators: ==, !=, >, <, >=, <=, =~ (regex)
    m = re.match(
        r'@(?:\.([a-zA-Z_][a-zA-Z0-9_]*))?\s*'
        r'(==|!=|>=|<=|>|<|=~)\s*'
        r'(.*)',
        expr
    )
    if not m:
        # Try partial: just @.field (truthy)
        m2 = re.match(r'@(?:\.([a-zA-Z_][a-zA-Z0-9_]*))?', expr)
        if m2:
            field = m2.group(1)
            def truthy(x):
                v = x.get(field) if field else x
                return bool(v) if v is not None else False
            return truthy
        return lambda x: True

    field_path = m.group(1)  # may be None
    op = m.group(2)
    raw_val = m.group(3).strip().strip("'\"")

    # Try to convert value to int/float
    try:
        val = int(raw_val)
    except ValueError:
        try:
            val = float(raw_val)
        except ValueError:
            val = raw_val  # keep as string

    def _get_val(item):
        if field_path:
            return item.get(field_path) if isinstance(item, dict) else None
        return item

    def _cmp(item):
        v = _get_val(item)
        if v is None:
            return False
        if op == '==': return v == val
        if op == '!=': return v != val
        if op == '>':  return (v if isinstance(v, (int, float)) else 0) > (val if isinstance(val, (int, float)) else 0)
        if op == '<':  return (v if isinstance(v, (int, float)) else 0) < (val if isinstance(val, (int, float)) else 0)
        if op == '>=': return (v if isinstance(v, (int, float)) else 0) >= (val if isinstance(val, (int, float)) else 0)
        if op == '<=': return (v if isinstance(v, (int, float)) else 0) <= (val if isinstance(val, (int, float)) else 0)
        if op == '=~': return bool(re.search(str(val), str(v)))
        return False

    return _cmp


def _resolve(data: Any, tokens: list) -> Any:
    """Resolve a list of tokens against data, returning matched result(s)."""
    if not tokens:
        return data

    tok = tokens[0]
    rest = tokens[1:]

    if tok[0] == 'key':
        key = tok[1]
        if isinstance(data, dict):
            val = data.get(key)
            return _resolve(val, rest) if rest else val
        return None

    if tok[0] == 'index':
        idx = tok[1]
        if isinstance(data, (list, tuple)):
            try:
                val = data[idx]
                return _resolve(val, rest) if rest else val
            except IndexError:
                return None
        return None

    if tok[0] == 'wildcard':
        if isinstance(data, (list, tuple)):
            results = []
            for item in data:
                if rest:
                    r = _resolve(item, rest)
                    if r is not None:
                        if isinstance(r, list):
                            results.extend(r)
                        else:
                            results.append(r)
                else:
                    results.append(item)
            return results
        elif isinstance(data, dict):
            results = []
            for v in data.values():
                if rest:
                    r = _resolve(v, rest)
                    if r is not None:
                        if isinstance(r, list):
                            results.extend(r)
                        else:
                            results.append(r)
                else:
                    results.append(v)
            return results
        return data

    if tok[0] == 'filter':
        predicate = _compile_filter(tok[1])
        if isinstance(data, list):
            results = []
            for item in data:
                if predicate(item):
                    if rest:
                        r = _resolve(item, rest)
                        if r is not None:
                            if isinstance(r, list):
                                results.extend(r)
                            else:
                                results.append(r)
                    else:
                        results.append(item)
            return results
        return data

    return None


def query(data: Any, path: str) -> Any:
    """Run a JSON path query against data.

    Args:
        data: Parsed JSON (dict/list/str/int/float/bool/None)
        path: JSON path expression like '$.users[?(@.age > 25)].name'

    Returns:
        Query result (list, dict, scalar, or None)
    """
    if not path or path == '$' or path == '.':
        return data
    tokens = _tokenize(path)
    return _resolve(data, tokens)


# ---------- CLI arg parsing ----------

def parse_args(argv: list = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog='jsonql',
        description='Zero-dependency JSON query tool for CLI. '
                    'Query, filter, and extract from JSON data.',
        epilog='Examples:\n'
               '  cat data.json | jsonql users\n'
               '  jsonql data.json "$.users[?(@.age > 25)].name"\n'
               '  curl api.example.com/users | jsonql -r "$[*].email"',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument('expr', nargs='*', default=[],
                   help='File path and/or JSON path expression. '
                        'If the first argument looks like a file path '
                        '(has an extension or is a file on disk), it is '
                        'treated as the input file. All remaining args '
                        'are joined as the JSON path.')
    p.add_argument('-r', '--raw', action='store_true',
                   help='Output raw strings only (no JSON formatting)')
    p.add_argument('-c', '--compact', action='store_true',
                   help='Compact JSON output (no indentation)')
    p.add_argument('-k', '--keys', action='store_true',
                   help='Output only keys for objects')
    return p.parse_args(argv)


def _resolve_args(expr_args: list) -> tuple:
    """Smart resolve: figure out which arg is file and which is path."""
    file_path = None
    path = '$'  # default

    if not expr_args:
        return None, '$'

    # Check if first arg is a file path
    first = expr_args[0]

    # Definitively a path expression, not a file
    if first.startswith('$') or '[' in first or '?' in first:
        return None, ' '.join(expr_args)

    # Check if it's an actual file on disk
    if os.path.isfile(first):
        file_path = first
        rest = expr_args[1:]
        if rest:
            path = ' '.join(rest)
        return file_path, path

    # Check extension heuristic: only treat as file if it looks like a filename
    # (has extension AND no special query chars in basename)
    base = os.path.basename(first)
    if '.' in base and not any(c in first for c in '?[@'):
        file_path = first
        rest = expr_args[1:]
        if rest:
            path = ' '.join(rest)
    else:
        path = ' '.join(expr_args)

    return file_path, path


def main(argv: list = None) -> int:
    args = parse_args(argv)
    file_path, path = _resolve_args(args.expr)

    # Read JSON
    try:
        if file_path:
            with open(file_path, 'r') as f:
                data = json.load(f)
        else:
            raw = sys.stdin.read()
            if not raw.strip():
                print("Error: no input (pipe JSON or provide file)", file=sys.stderr)
                return 1
            data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON — {e}", file=sys.stderr)
        return 1
    except FileNotFoundError:
        print(f"Error: file not found — {file_path}", file=sys.stderr)
        return 1

    # Run query
    result = query(data, path)

    # Handle None
    if result is None:
        return 0

    # Output
    if args.keys and isinstance(result, dict):
        for k in result:
            print(k)
    elif args.raw:
        if isinstance(result, list):
            for item in result:
                print(item)
        else:
            print(result)
    else:
        indent = None if args.compact else 2
        # Ensure ASCII safe output
        print(json.dumps(result, indent=indent, ensure_ascii=False, default=str))

    return 0



# === Auto-registration metadata ===
TOOL_META = {
    "name": "jsonql",
    "func": "main",
    "desc": 'SQL-like JSON query engine',
}

if __name__ == '__main__':
    sys.exit(main())
