#!/usr/bin/env python3
"""case-convert — Convert text between case styles.

Usage: case-convert <text> [--to <style>]
       echo "helloWorld" | case-convert --to snake
       case-convert "my_var_name" --to camel

Styles: snake, camel, kebab, pascal, title, const, dot, slash
"""

import sys
import re


def _split_words(text):
    text = text.replace("-", " ").replace("_", " ").replace(".", " ").replace("/", " ")
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    text = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', text)
    return text.lower().split()


def main():
    args = sys.argv[1:]
    if '-h' in args or '--help' in args:
        print(__doc__)
        return
    target = "snake"
    if '--to' in args:
        idx = args.index('--to')
        if idx + 1 < len(args):
            target = args[idx + 1]
            args = args[:idx] + args[idx + 2:]
    if args:
        text = ' '.join(args)
    else:
        text = sys.stdin.read().strip()
    words = _split_words(text)
    if not words:
        return
    result = {
        'snake': '_'.join(words),
        'kebab': '-'.join(words),
        'camel': words[0] + ''.join(w.capitalize() for w in words[1:]),
        'pascal': ''.join(w.capitalize() for w in words),
        'title': ' '.join(w.capitalize() for w in words),
        'const': '_'.join(w.upper() for w in words),
        'dot': '.'.join(words),
        'slash': '/'.join(words),
    }
    print(result.get(target, words))
    if '--all' in sys.argv[1:]:
        print()
        for style, val in result.items():
            print(f"  {style:<8} {val}")


TOOL_META = {
    "name": "case-convert",
    "func": "main",
    "desc": "Convert text between case styles (snake/camel/kebab/pascal/title/const)"
}
