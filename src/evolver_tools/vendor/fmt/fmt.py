#!/usr/bin/env python3
"""fmt — Code/text formatter

Auto-fix common formatting issues: trailing whitespace, line endings, EOF newline.

Usage:
    fmt file.py              # Format file in-place
    fmt --check file.py      # Check-only (exit 1 if changes needed)
    cat messy.txt | fmt      # Format stdin → stdout
    fmt --tabs=4 file.py     # Convert leading spaces to 4-space or tab
"""
import sys
import os
import re


def strip_trailing_whitespace(lines):
    """Strip trailing whitespace from each line."""
    return [line.rstrip() for line in lines]


def ensure_final_newline(lines):
    """Ensure file ends with exactly one newline."""
    while lines and lines[-1] == '':
        lines = lines[:-1]
    if not lines:
        return ['']
    lines.append('')
    return lines


def normalize_line_endings(text):
    """Normalize \\r\\n to \\n."""
    return text.replace('\r\n', '\n')


def fix_indentation(lines, tab_size=None):
    """If tab_size is set, convert leading tabs to spaces or vice versa."""
    if tab_size is None:
        return lines
    if tab_size == 0:
        # Convert leading spaces to tabs (1 tab = 4 spaces by default for detection)
        result = []
        for line in lines:
            stripped = line.lstrip()
            leading = line[:len(line) - len(stripped)]
            # Count leading spaces
            spaces = len(leading)
            tabs = spaces // 4
            extra = spaces % 4
            result.append('\t' * tabs + ' ' * extra + stripped)
        return result
    else:
        # Convert leading tabs to spaces
        result = []
        for line in lines:
            stripped = line.lstrip('\t')
            leading_tabs = len(line) - len(stripped) - len(line.lstrip())
            leading_tabs = len(line) - len(stripped)
            result.append(' ' * (leading_tabs * tab_size) + stripped)
        return result


def format_text(text, tab_size=None):
    """Apply all formatting rules."""
    text = normalize_line_endings(text)
    lines = text.split('\n')
    # Remove trailing empty line from split
    if lines and lines[-1] == '':
        lines = lines[:-1]
    lines = strip_trailing_whitespace(lines)
    lines = fix_indentation(lines, tab_size)
    lines = ensure_final_newline(lines)
    return '\n'.join(lines)


def main():
    args = sys.argv[1:]

    if not args:
        # stdin mode
        text = sys.stdin.read()
        formatted = format_text(text)
        sys.stdout.write(formatted)
        return

    if args[0] in ('-h', '--help'):
        print(__doc__.strip())
        return

    check_only = False
    tab_size = None
    files = []

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == '--check':
            check_only = True
        elif arg.startswith('--tabs='):
            val = arg.split('=', 1)[1]
            tab_size = int(val) if val.lower() not in ('tab', 't') else 0
        elif arg == '--tabs':
            i += 1
            if i < len(args):
                val = args[i]
                tab_size = int(val) if val.lower() not in ('tab', 't') else 0
        elif arg.startswith('-'):
            print(f"Error: unknown option '{arg}'", file=sys.stderr)
            sys.exit(1)
        else:
            files.append(arg)
        i += 1

    if not files:
        text = sys.stdin.read()
        formatted = format_text(text, tab_size)
        sys.stdout.write(formatted)
        return

    any_changes = False
    for filepath in files:
        if not os.path.isfile(filepath):
            print(f"Error: file not found: {filepath}", file=sys.stderr)
            sys.exit(1)
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            original = f.read()
        formatted = format_text(original, tab_size)
        if original != formatted:
            any_changes = True
            if check_only:
                print(f"Would format: {filepath}")
            else:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(formatted)
                print(f"Formatted: {filepath}")

    if check_only and any_changes:
        sys.exit(1)


if __name__ == '__main__':
    main()
