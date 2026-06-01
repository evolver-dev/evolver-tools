#!/usr/bin/env python3
"""seq — Generate sequence of numbers.

Usage: seq 10           # 1 2 3 ... 10
       seq 5 10         # 5 6 7 ... 10
       seq 0 2 10       # 0 2 4 ... 10
       seq -s ', ' 1 5  # 1, 2, 3, 4, 5

Like standard Unix 'seq' command.
Zero-dependency (stdlib only).
"""

import sys


def main():
    args = sys.argv[1:]
    sep = '\n'

    filtered = []
    i = 0
    while i < len(args):
        if args[i] == '-s' and i + 1 < len(args):
            sep = args[i + 1]
            i += 2
        elif args[i].startswith('-s'):
            sep = args[i][2:]
            i += 1
        elif args[i] in ('-h', '--help'):
            print(__doc__)
            return
        else:
            filtered.append(args[i])
            i += 1

    if not filtered:
        print("Usage: seq <last> or seq <first> <last> or seq <first> <step> <last>")
        return

    try:
        nums = [float(a) for a in filtered]
    except ValueError:
        print("Error: arguments must be numbers", file=sys.stderr)
        sys.exit(1)

    if len(nums) == 1:
        first, step, last = 1.0, 1.0, nums[0]
    elif len(nums) == 2:
        first, last = nums
        step = 1.0 if first <= last else -1.0
    elif len(nums) == 3:
        first, step, last = nums
    else:
        print("Error: too many arguments", file=sys.stderr)
        sys.exit(1)

    if step == 0:
        print("Error: step cannot be zero", file=sys.stderr)
        sys.exit(1)

    result = []
    if step > 0:
        val = first
        while val <= last:
            result.append(str(int(val) if val == int(val) else val))
            val += step
    else:
        val = first
        while val >= last:
            result.append(str(int(val) if val == int(val) else val))
            val += step

    print(sep.join(result))


# === Auto-registration metadata ===
TOOL_META = {
    "name": "seq",
    "func": "main",
    "desc": 'Generate sequence of numbers',
}

if __name__ == '__main__':
    main()
