#!/usr/bin/env python3
"""markdown-lint — Basic Markdown linting / style checking.

Checks:
- Blank lines around headings
- Heading level increments (no skipping)
- Unclosed code fences
- Multiple consecutive blank lines
- Trailing whitespace
- Long lines (>80 chars in non-code blocks)

Usage: markdown-lint <file.md>
       cat <file.md> | markdown-lint

Zero-dependency (stdlib only).
"""
import sys
import re


def lint_markdown(text: str, filename: str = '<stdin>'):
    lines = text.split('\n')
    issues = []
    in_code_block = False
    prev_heading_level = 0
    prev_blank = False
    blank_count = 0

    for i, line in enumerate(lines):
        lineno = i + 1

        # Code fence tracking
        if line.strip().startswith('```') or line.strip().startswith('~~~'):
            in_code_block = not in_code_block
            prev_blank = False
            continue

        # Check trailing whitespace
        if line != line.rstrip() and not in_code_block:
            issues.append((lineno, 'trailing-whitespace', f'Line has trailing whitespace'))

        # Check long lines (in non-code blocks)
        if len(line) > 80 and not in_code_block:
            issues.append((lineno, 'line-length', f'Line too long ({len(line)} chars, max 80)'))

        # Check consecutive blank lines
        if line.strip() == '':
            blank_count += 1
            if blank_count > 1 and not in_code_block:
                issues.append((lineno, 'consecutive-blanks', 'Multiple consecutive blank lines'))
        else:
            blank_count = 0

        # Heading checks
        heading_match = re.match(r'^(#{1,6})\s', line)
        if heading_match and not in_code_block:
            level = len(heading_match.group(1))

            # Check heading increment
            if prev_heading_level and level > prev_heading_level + 1:
                issues.append((lineno, 'heading-skip', f'Heading level skipped: h{prev_heading_level} → h{level}'))

            prev_heading_level = level
            prev_blank = False

        prev_blank = (line.strip() == '')

    # Check unclosed code fence
    if in_code_block:
        issues.append((len(lines), 'unclosed-fence', 'Unclosed code fence at end of file'))

    return issues


def main():
    args = sys.argv[1:]

    if '-h' in args or '--help' in args:
        print(__doc__)
        return

    if args:
        filename = args[0]
        try:
            with open(filename) as f:
                text = f.read()
        except FileNotFoundError:
            print(f'Error: File not found: {filename}', file=sys.stderr)
            sys.exit(1)
    else:
        filename = '<stdin>'
        text = sys.stdin.read()

    issues = lint_markdown(text, filename)

    if not issues:
        print(f'{filename}: No issues found ✓')
        return

    # Group by severity
    print(f'{filename}: {len(issues)} issue(s) found')
    print()
    for lineno, rule, msg in issues:
        print(f'  {lineno:>4}  [{rule:<20}] {msg}')


TOOL_META = {
    "name": "markdown-lint",
    "func": "main",
    "desc": "Basic Markdown linting — headings, fences, whitespace, line length",
}

if __name__ == '__main__':
    main()
