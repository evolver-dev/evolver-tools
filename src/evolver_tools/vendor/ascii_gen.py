#!/usr/bin/env python3
"""ascii-gen — ASCII art generator (patterns, borders, colorized).

Usage: ascii-gen --style=box <text>
       echo "Hello" | ascii-gen --style=star
       ascii-gen --style=pattern --width=40 --height=10

Styles: box, star, heart, arrow, banner, checker, diamond, tree

Zero-dependency (stdlib only).
"""

import sys, textwrap

STYLES = {}

def register(name):
    def decorator(fn):
        STYLES[name] = fn
        return fn
    return decorator

@register('box')
def make_box(text, width=0):
    lines = text.splitlines() if text else ['']
    if width == 0:
        width = max(len(l) for l in lines) + 4
    top = '╔' + '═' * (width-2) + '╗'
    bottom = '╚' + '═' * (width-2) + '╝'
    result = [top]
    for line in lines:
        result.append('║ ' + line.ljust(width-4) + ' ║')
    result.append(bottom)
    return '\n'.join(result)

@register('star')
def make_star(text, width=0):
    lines = text.splitlines() if text else ['*']
    border = '*' * (max(len(l) for l in lines) + 6)
    result = [border]
    for line in lines:
        result.append(f'** {line} **')
    result.append(border)
    return '\n'.join(result)

@register('banner')
def make_banner(text, width=0):
    lines = text.splitlines() if text else ['']
    if width == 0:
        width = max(len(l) for l in lines) + 4
    top = '█' * width
    bot = '█' * width
    result = [top]
    for line in lines:
        pad = width - len(line) - 2
        result.append('█' + line + ' ' * pad + '█')
    result.append(bot)
    return '\n'.join(result)

@register('heart')
def make_heart(text, width=0):
    h = ['  ██╗  ██╗ █████╗ ██████╗ ████████╗',
         '  ██║  ██║██╔══██╗██╔══██╗╚══██╔══╝',
         '  ███████║███████║██████╔╝   ██║   ',
         '  ██╔══██║██╔══██║██╔══██╗   ██║   ',
         '  ██║  ██║██║  ██║██║  ██║   ██║   ',
         '  ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ']
    return '\n'.join(h)

@register('checker')
def make_checker(text, width=40, height=10):
    """Checkerboard pattern."""
    rows = []
    for y in range(height):
        row = ''
        for x in range(width):
            if (x + y) % 2 == 0:
                row += '█'
            else:
                row += ' '
        rows.append(row)
    return '\n'.join(rows)

@register('diamond')
def make_diamond(text, size=5):
    rows = []
    for i in range(size):
        rows.append(' ' * (size-i-1) + '/' + ' ' * (i*2) + '\\')
    for i in range(size-1, -1, -1):
        rows.append(' ' * (size-i-1) + '\\' + ' ' * (i*2) + '/')
    return '\n'.join(rows)

@register('tree')
def make_tree(text, size=5):
    rows = []
    for i in range(size):
        rows.append(' ' * (size-i-1) + '*' * (i*2+1))
    rows.append(' ' * (size-1) + '|')
    return '\n'.join(rows)

def main():
    args = sys.argv[1:]
    style = 'box'
    width = 0
    height = 10
    size = 5
    text_lines = []

    i = 0
    while i < len(args):
        a = args[i]
        if a.startswith('--style='):
            style = a.split('=', 1)[1]
        elif a.startswith('--width='):
            width = int(a.split('=', 1)[1])
        elif a.startswith('--height='):
            height = int(a.split('=', 1)[1])
        elif a.startswith('--size='):
            size = int(a.split('=', 1)[1])
        elif a.startswith('-'):
            print(f"Usage: ascii-gen [--style=box|star|heart|banner|checker|diamond|tree] [--width=N] [--size=N] [text]")
            return
        else:
            text_lines.append(a)
        i += 1

    text = ' '.join(text_lines)
    if not text and not sys.stdin.isatty():
        text = sys.stdin.read().strip()

    if style not in STYLES:
        print(f"Unknown style: {style}. Available: {', '.join(STYLES.keys())}", file=sys.stderr)
        sys.exit(1)

    result = STYLES[style](text, width) if style in ('box', 'star', 'banner') else \
             STYLES[style](text, width, height) if style == 'checker' else \
             STYLES[style](text, size) if style in ('diamond', 'tree') else \
             STYLES[style](text)
    print(result)


# === Auto-registration metadata ===
TOOL_META = {
    "name": "ascii-gen",
    "func": "main",
    "desc": 'ASCII art generator (8 styles)',
}

if __name__ == '__main__':
    main()
