#!/usr/bin/env python3
"""tr — Translate or delete characters.

Usage: tr 'abc' 'xyz'      # replace a->x, b->y, c->z
       echo "hello" | tr 'a-z' 'A-Z'   # uppercase
       tr -d 'aeiou'        # delete vowels
       tr -s ' '            # squeeze spaces

Like standard Unix 'tr' command.
Zero-dependency (stdlib only).
"""

import sys
import re


def expand_range(pattern):
    """Expand a-z style ranges."""
    result = ''
    i = 0
    while i < len(pattern):
        if i + 2 < len(pattern) and pattern[i + 1] == '-':
            start = ord(pattern[i])
            end = ord(pattern[i + 2])
            if start <= end:
                result += ''.join(chr(c) for c in range(start, end + 1))
                i += 3
                continue
        result += pattern[i]
        i += 1
    return result


def main():
    args = sys.argv[1:]
    delete = False
    squeeze = False

    filtered = []
    for a in args:
        if a == '-d':
            delete = True
        elif a == '-s':
            squeeze = True
        elif a in ('-h', '--help'):
            print(__doc__)
            return
        else:
            filtered.append(a)

    if not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        print("Usage: echo <text> | tr [options] <set1> [<set2>]")
        print("       tr -d <set1>")
        print("       tr -s <set1>")
        return

    if delete:
        if not filtered:
            return
        set1 = expand_range(filtered[0])
        trans = str.maketrans('', '', set1)
        result = text.translate(trans)
        print(result, end='')
        return

    if squeeze:
        if not filtered:
            return
        set1 = expand_range(filtered[0])
        pattern = '[' + re.escape(set1) + ']+'
        result = re.sub(pattern, lambda m: m.group(0)[0], text)
        print(result, end='')
        return

    if len(filtered) < 2:
        print("Error: need two character sets", file=sys.stderr)
        return

    set1 = expand_range(filtered[0])
    set2 = expand_range(filtered[1])

    # Pad set2 if shorter
    if len(set2) < len(set1):
        set2 += set2[-1] * (len(set1) - len(set2))

    trans = str.maketrans(set1, set2)
    result = text.translate(trans)
    print(result, end='')


# === Auto-registration metadata ===
TOOL_META = {
    "name": "tr",
    "func": "main",
    "desc": 'Translate or delete characters (stdin)',
}

if __name__ == '__main__':
    main()
