#!/usr/bin/env python3
"""json-pretty — JSON pretty printer, formatter, validator

Pretty-print, validate, minify, and sort JSON from files or stdin.

Usage:
    json-pretty data.json            # Pretty-print file
    json-pretty data.json data2.json # Multiple files
    cat ugly.json | json-pretty      # Pretty-print stdin
    json-pretty --minify data.json   # Minify (single line)
    json-pretty --validate data.json # Validate only (exit code)
    json-pretty --sort data.json     # Sort keys alphabetically
    json-pretty --indent=4 data.json # Custom indent width
"""
import sys
import os
import json


def pretty_print(text, indent=2, sort_keys=False):
    """Pretty-print JSON."""
    data = json.loads(text)
    return json.dumps(data, indent=indent, ensure_ascii=False, sort_keys=sort_keys) + '\n'


def minify(text):
    """Minify JSON to single line."""
    data = json.loads(text)
    return json.dumps(data, ensure_ascii=False, separators=(',', ':')) + '\n'


def validate(text):
    """Validate JSON, return (is_valid, error_msg)."""
    try:
        json.loads(text)
        return True, None
    except json.JSONDecodeError as e:
        return False, str(e)


def main():
    args = sys.argv[1:]

    do_minify = False
    do_validate = False
    do_sort = False
    indent = 2
    files = []

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ('-h', '--help'):
            print(__doc__.strip())
            return
        elif arg == '--minify':
            do_minify = True
        elif arg == '--validate':
            do_validate = True
        elif arg == '--sort':
            do_sort = True
        elif arg.startswith('--indent='):
            indent = int(arg.split('=', 1)[1])
        elif arg.startswith('-'):
            print(f"Error: unknown option '{arg}'", file=sys.stderr)
            sys.exit(1)
        else:
            files.append(arg)
        i += 1

    if not files:
        # Stdin mode
        text = sys.stdin.read()
        if do_validate:
            valid, err = validate(text)
            if valid:
                print("Valid JSON")
            else:
                print(f"Invalid JSON: {err}", file=sys.stderr)
                sys.exit(1)
            return
        try:
            if do_minify:
                result = minify(text)
            else:
                result = pretty_print(text, indent, do_sort)
            sys.stdout.write(result)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}", file=sys.stderr)
            sys.exit(1)
        return

    for filepath in files:
        if not os.path.isfile(filepath):
            print(f"Error: file not found: {filepath}", file=sys.stderr)
            sys.exit(1)
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()

        if do_validate:
            valid, err = validate(text)
            status = "✓" if valid else "✗"
            print(f"{status} {filepath}")
            if not valid:
                print(f"   {err}", file=sys.stderr)
            continue

        try:
            if do_minify:
                result = minify(text)
            else:
                result = pretty_print(text, indent, do_sort)
            sys.stdout.write(result)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON ({filepath}): {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == '__main__':
    main()
