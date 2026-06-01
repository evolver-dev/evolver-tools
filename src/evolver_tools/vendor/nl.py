#!/usr/bin/env python3
"""nl — Number lines of files or stdin.

Usage: nl <file>
       cat <file> | nl [-ba]  # -a=number all, -b=number non-empty
       nl -s '. ' input.txt   # custom separator

Like standard Unix 'nl' command.
Zero-dependency (stdlib only).
"""

import sys


def main():
    args = sys.argv[1:]
    style = 't'  # t = non-empty only, a = all, n = none
    separator = '  '
    start_num = 1

    filtered = []
    i = 0
    while i < len(args):
        if args[i] == '-ba':
            style = 'a'
            i += 1
        elif args[i] == '-bt':
            style = 't'
            i += 1
        elif args[i] == '-bn':
            style = 'n'
            i += 1
        elif args[i] == '-s' and i + 1 < len(args):
            separator = args[i + 1]
            i += 2
        elif args[i].startswith('-s'):
            separator = args[i][2:]
            i += 1
        elif args[i] == '-v' and i + 1 < len(args):
            start_num = int(args[i + 1])
            i += 2
        elif args[i] in ('-h', '--help'):
            print(__doc__)
            return
        else:
            filtered.append(args[i])
            i += 1

    if filtered:
        for path in filtered:
            try:
                with open(path) as f:
                    lines = f.readlines()
            except FileNotFoundError:
                print(f"Error: file not found: {path}", file=sys.stderr)
                continue
            lineno = start_num
            for line in lines:
                numbered = False
                if style == 'a' or (style == 't' and line.strip()):
                    print(f'{lineno:>6}{separator}{line}', end='')
                    lineno += 1
                    numbered = True
                if not numbered:
                    print(f'       {separator}{line}', end='')
    elif not sys.stdin.isatty():
        lines = sys.stdin.readlines()
        lineno = start_num
        for line in lines:
            numbered = False
            if style == 'a' or (style == 't' and line.strip()):
                print(f'{lineno:>6}{separator}{line}', end='')
                lineno += 1
                numbered = True
            if not numbered:
                print(f'       {separator}{line}', end='')
    else:
        print("Usage: nl <file> or cat <file> | nl")
        return


# === Auto-registration metadata ===
TOOL_META = {
    "name": "nl",
    "func": "main",
    "desc": 'Number lines of files or stdin',
}

if __name__ == '__main__':
    main()
