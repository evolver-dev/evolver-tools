#!/usr/bin/env python3
"""yaml2json — Convert YAML to JSON (zero dependencies, basic YAML subset)

Parses common YAML: key: value, nested dicts, lists (- items), quoted strings,
multi-line (|, >), inline flow {} and [].

Usage:
    yaml2json config.yaml          # File → stdout
    cat data.yaml | yaml2json      # Stdin → stdout
    yaml2json --pretty config.yaml # Pretty-print JSON
"""
import sys
import os
import json
import re


def parse_yaml(text):
    """Parse a subset of YAML to Python dict/list."""
    lines = text.split('\n')
    # Strip trailing empty
    while lines and lines[-1].strip() == '':
        lines = lines[:-1]

    # Build indent-based tree
    # Returns (result, consumed_indices)
    return _parse_block(lines, 0, 0)[0]


def _get_indent(line):
    return len(line) - len(line.lstrip())


def _parse_block(lines, start, min_indent):
    """Parse a block at given indent level. Returns (value, next_index)."""
    result = None
    i = start
    in_block_scalar = False
    block_scalar_lines = []
    block_scalar_indent = None
    block_scalar_style = None  # '|' literal, '>' folded

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Handle block scalar continuation
        if in_block_scalar:
            indent = _get_indent(line)
            if indent > block_scalar_indent:
                block_scalar_lines.append(line)
                i += 1
                continue
            else:
                # End of block scalar
                in_block_scalar = False
                if block_scalar_style == '>':
                    text = ' '.join(block_scalar_lines)
                else:
                    text = '\n'.join(block_scalar_lines)
                result = text
                continue

        if stripped == '' or stripped.startswith('#'):
            i += 1
            continue

        indent = _get_indent(line)
        if indent < min_indent:
            break

        if indent == min_indent:
            # Check for list item
            list_match = re.match(r'^(\s*)-\s+(.*)', line)
            if list_match:
                items = []
                while i < len(lines):
                    line2 = lines[i]
                    stripped2 = line2.strip()
                    if stripped2 == '' or stripped2.startswith('#'):
                        i += 1
                        continue
                    m = re.match(r'^(\s*)-\s+(.*)', line2)
                    if not m:
                        break
                    item_indent = len(m.group(1))
                    if item_indent < min_indent:
                        break
                    rest = m.group(2).strip()

                    # Block scalar with -
                    if rest in ('|', '>'):
                        block_scalar_style = rest
                        in_block_scalar = True
                        block_scalar_lines = []
                        block_scalar_indent = _get_indent(line2) + 1
                        item_value = _parse_scalar(rest)  # Will be overwritten
                        # Actually, we need to collect it
                        i += 1
                        continue
                    elif rest == '':
                        # Sub-item (nested under -)
                        sub = _parse_block(lines, i + 1, _get_indent(line2) + 1)
                        if sub[0] is not None:
                            items.append(sub[0])
                        i = sub[1]
                        continue
                    else:
                        # Scalar or mapping
                        colon_idx = _find_colon(rest)
                        if colon_idx >= 0:
                            key = rest[:colon_idx].strip()
                            val = rest[colon_idx + 1:].strip()
                            d = {}
                            if val == '':
                                d[key] = _parse_block(lines, i + 1, _get_indent(line2) + 1)[0]
                            else:
                                d[key] = _parse_scalar(val)
                            items.append(d)
                        else:
                            items.append(_parse_scalar(rest))
                        i += 1
                result = items
                return (result, i)

            # Key: value mapping
            colon_idx = _find_colon(stripped)
            if colon_idx >= 0:
                key = stripped[:colon_idx].strip()
                val = stripped[colon_idx + 1:].strip()

                # String value that's actually the key itself (no colon ambiguity)
                if colon_idx < 0:
                    i += 1
                    continue

                if result is None:
                    result = {}

                if val in ('|', '>'):
                    # Block scalar
                    block_scalar_style = val
                    in_block_scalar = True
                    block_scalar_lines = []
                    block_scalar_indent = indent + 1
                    result[key] = ''  # placeholder, will be updated
                    i += 1
                elif val == '':
                    # Nested block
                    sub = _parse_block(lines, i + 1, indent + 1)
                    result[key] = sub[0]
                    i = sub[1]
                else:
                    result[key] = _parse_scalar(val)
                    i += 1
            else:
                # Plain scalar
                result = _parse_scalar(stripped)
                i += 1
        else:
            break

    # Clean up any trailing block scalar
    if in_block_scalar:
        if block_scalar_style == '>':
            text = ' '.join(block_scalar_lines)
        else:
            text = '\n'.join(block_scalar_lines)
        # Find the last key in result and set it
        if isinstance(result, dict):
            for k in list(result.keys()):
                if result[k] == '' or result[k] is None:
                    result[k] = text
                    break

    return (result, i)


def _find_colon(s):
    """Find colon that's not inside quotes."""
    in_sq = False
    in_dq = False
    for i, ch in enumerate(s):
        if ch == "'" and not in_dq:
            in_sq = not in_sq
        elif ch == '"' and not in_sq:
            in_dq = not in_dq
        elif ch == ':' and not in_sq and not in_dq:
            return i
    return -1


def _parse_scalar(s):
    """Parse a YAML scalar value."""
    if s == 'null' or s == '~':
        return None
    if s == 'true' or s == 'True' or s == 'yes' or s == 'on':
        return True
    if s == 'false' or s == 'False' or s == 'no' or s == 'off':
        return False

    # Integer
    try:
        return int(s)
    except ValueError:
        pass

    # Float
    try:
        return float(s)
    except ValueError:
        pass

    # Quoted strings
    if len(s) >= 2:
        if (s[0] == "'" and s[-1] == "'") or (s[0] == '"' and s[-1] == '"'):
            return s[1:-1]

    # Inline flow mapping {}
    if s.startswith('{') and s.endswith('}'):
        inner = s[1:-1].strip()
        d = {}
        if inner:
            for pair in _split_flow(inner):
                k, v = pair.split(':', 1)
                d[k.strip()] = _parse_scalar(v.strip())
        return d

    # Inline flow list []
    if s.startswith('[') and s.endswith(']'):
        inner = s[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(item.strip()) for item in _split_flow(inner)]

    return s


def _split_flow(s):
    """Split comma-separated flow items respecting quotes and nesting."""
    items = []
    depth = 0
    in_sq = False
    in_dq = False
    current = ''
    for ch in s:
        if ch == "'" and not in_dq:
            in_sq = not in_sq
            current += ch
        elif ch == '"' and not in_sq:
            in_dq = not in_dq
            current += ch
        elif ch in ('{', '['):
            depth += 1
            current += ch
        elif ch in ('}', ']'):
            depth -= 1
            current += ch
        elif ch == ',' and depth == 0 and not in_sq and not in_dq:
            items.append(current)
            current = ''
        else:
            current += ch
    if current.strip():
        items.append(current)
    return items


def main():
    args = sys.argv[1:]

    if not args:
        text = sys.stdin.read()
        data = parse_yaml(text)
        json.dump(data, sys.stdout, ensure_ascii=False)
        sys.stdout.write('\n')
        return

    if args[0] in ('-h', '--help'):
        print(__doc__.strip())
        return

    pretty = '--pretty' in args or '-p' in args
    files = [a for a in args if not a.startswith('-')]

    if not files:
        text = sys.stdin.read()
        data = parse_yaml(text)
        if pretty:
            json.dump(data, sys.stdout, indent=2, ensure_ascii=False)
        else:
            json.dump(data, sys.stdout, ensure_ascii=False)
        sys.stdout.write('\n')
        return

    for filepath in files:
        if not os.path.isfile(filepath):
            print(f"Error: file not found: {filepath}", file=sys.stderr)
            sys.exit(1)
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read()
        data = parse_yaml(text)
        if pretty:
            json.dump(data, sys.stdout, indent=2, ensure_ascii=False)
        else:
            json.dump(data, sys.stdout, ensure_ascii=False)
        sys.stdout.write('\n')


if __name__ == '__main__':
    main()
