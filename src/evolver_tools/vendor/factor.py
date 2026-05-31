#!/usr/bin/env python3
"""factor — Prime factorization of integers.

Usage: factor 123
       factor 12 15 21
       echo "100" | factor

Like standard Unix 'factor' command.
Zero-dependency (stdlib only).
"""

import sys
import math


def factorize(n):
    """Return list of prime factors for n."""
    n = int(n)
    if n < 2:
        return []
    factors = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1 if d == 2 else 2  # skip evens after 2
    if n > 1:
        factors.append(n)
    return factors


def main():
    args = sys.argv[1:]

    if '-h' in args or '--help' in args:
        print(__doc__)
        return

    numbers = []

    if args:
        for a in args:
            try:
                numbers.append(int(a))
            except ValueError:
                pass
    elif not sys.stdin.isatty():
        data = sys.stdin.read().strip()
        for token in data.split():
            try:
                numbers.append(int(token))
            except ValueError:
                pass

    if not numbers:
        print("Usage: factor <number> [number...]")
        print("       echo <number> | factor")
        return

    for n in numbers:
        if n < 2:
            print(f"{n}: {n}")
        else:
            factors = factorize(n)
            if len(factors) == 1:
                print(f"{n}: {n}")
            else:
                print(f"{n}: {' '.join(str(f) for f in factors)}")


# === Auto-registration metadata ===
TOOL_META = {
    "name": "factor",
    "func": "main",
    "desc": 'Prime factorization of integers',
}

if __name__ == '__main__':
    main()
