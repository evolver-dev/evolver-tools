#!/usr/bin/env python3
"""fold — Wrap input lines to a specified width.

Usage: fold <file>          # wrap at 80
       fold -w 40 <file>    # wrap at 40
       echo "long text" | fold -w 20 -s   # break at spaces

Like standard Unix 'fold' command.
Zero-dependency (stdlib only).
"""

import sys


def fold_line(line, width, spaces=False):
    """Fold a single line to given width."""
    if len(line) <= width or (len(line) == width + 1 and line.endswith('\n')):
        return line

    result = []
    while line:
        if len(line) <= width:
            result.append(line)
            break

        chunk = line[:width]
        if spaces:
            # Find last space in the chunk
            last_space = chunk.rfind(' ')
            if last_space > 0:
                result.append(line[:last_space] + '\n')
                line = line[last_space:].lstrip()
                continue

        result.append(chunk.rstrip('\n') + '\n')
        line = line[width:]
    return ''.join(result)


def main():
    args = sys.argv[1:]
    width = 80
    spaces = False

    filtered = []
    i = 0
    while i < len(args):
        if args[i] == '-w' and i + 1 < len(args):
            width = int(args[i + 1])
            i += 2
        elif args[i].startswith('-w'):
            width = int(args[i][2:])
            i += 1
        elif args[i] == '-s':
            spaces = True
            i += 1
        elif args[i] in ('-h', '--help'):
            print(__doc__)
            return
        else:
            filtered.append(args[i])
            i += 1

    if filtered:
        for path in filtered:
            with open(path) as f:
                for line in f:
                    print(fold_line(line.rstrip('\n'), width, spaces))
    elif not sys.stdin.isatty():
        for line in sys.stdin:
            print(fold_line(line.rstrip('\n'), width, spaces))
    else:
        print("Usage: fold [-w <width>] [-s] <file>")
        print("       cat <file> | fold [-w 40]")


# === Auto-registration metadata ===
TOOL_META = {
    "name": "fold",
    "func": "main",
    "desc": 'Wrap input lines to specified width',
}

if __name__ == '__main__':
    main()
