#!/usr/bin/env python3
"""json-diff — Deep diff two JSON files, show paths that differ.

Usage: json-diff <file1> <file2>
       json-diff -- <json1> <json2>

Zero-dependency (stdlib only).
"""
import sys
import json


def deep_diff(a, b, path=''):
    """Recursively compare two values and yield differing paths."""
    if type(a) != type(b):
        yield f'{path}: type mismatch ({type(a).__name__} vs {type(b).__name__})'
        yield f'  - {json.dumps(a, ensure_ascii=False)[:200]}'
        yield f'  + {json.dumps(b, ensure_ascii=False)[:200]}'
        return

    if isinstance(a, dict):
        all_keys = set(a) | set(b)
        for k in sorted(all_keys):
            new_path = f'{path}.{k}' if path else k
            if k not in a:
                yield f'{new_path}: added'
                yield f'  + {json.dumps(b[k], ensure_ascii=False)[:200]}'
            elif k not in b:
                yield f'{new_path}: removed'
                yield f'  - {json.dumps(a[k], ensure_ascii=False)[:200]}'
            else:
                yield from deep_diff(a[k], b[k], new_path)
    elif isinstance(a, list):
        max_len = max(len(a), len(b))
        for i in range(max_len):
            new_path = f'{path}[{i}]'
            if i >= len(a):
                yield f'{new_path}: added'
                yield f'  + {json.dumps(b[i], ensure_ascii=False)[:200]}'
            elif i >= len(b):
                yield f'{new_path}: removed'
                yield f'  - {json.dumps(a[i], ensure_ascii=False)[:200]}'
            else:
                yield from deep_diff(a[i], b[i], new_path)
    else:
        if a != b:
            yield f'{path}: changed'
            yield f'  - {json.dumps(a, ensure_ascii=False)[:200]}'
            yield f'  + {json.dumps(b, ensure_ascii=False)[:200]}'


def main():
    args = sys.argv[1:]

    if '-h' in args or '--help' in args or len(args) != 2:
        print(__doc__)
        return

    try:
        if args[0] == '--':
            data1 = json.loads(args[1])
        else:
            with open(args[0]) as f:
                data1 = json.load(f)
    except Exception as e:
        print(f'Error reading {args[0]}: {e}', file=sys.stderr)
        sys.exit(1)

    try:
        if args[1] == '--':
            data2 = json.loads(args[0])
        else:
            with open(args[1]) as f:
                data2 = json.load(f)
    except Exception as e:
        print(f'Error reading {args[1]}: {e}', file=sys.stderr)
        sys.exit(1)

    diffs = list(deep_diff(data1, data2))
    if diffs:
        print(f'{len(diffs) // 2} difference(s) found:')
        print()
        for line in diffs:
            print(line)
    else:
        print('No differences — files are identical.')


TOOL_META = {
    "name": "json-diff",
    "func": "main",
    "desc": "Deep diff two JSON files, show paths that differ",
}

if __name__ == '__main__':
    main()
