#!/usr/bin/env python3
"""random-cli — Random data generator for various data types.

Generates random numbers, strings, UUIDs, hex, passwords,
choices, booleans. Supports count, range, seed, and CSV output.

Usage:
    random-cli --int                    # Random integer 0-100
    random-cli --float                  # Random float 0-100
    random-cli --string                 # Random 12-char string
    random-cli --uuid                   # Random UUID v4
    random-cli --hex                    # Random 12-char hex
    random-cli --pass                   # Random 12-char password
    random-cli --bool                   # Random boolean
    random-cli --choice a,b,c           # Random choice
    random-cli --int --min 10 --max 50  # Random int in range
    random-cli --string --len 8 -n 5    # 5 strings of length 8
    random-cli --int --float --csv -n 3 # CSV output, 3 each
    random-cli --seed 42 --int          # Reproducible results
"""

import argparse
import random
import string
import sys
import uuid

TOOL_META = {
    'name': 'random-cli',
    'func': 'main',
    'desc': 'Random data generator (numbers, strings, UUIDs, passwords)',
}


def _rand_int(min_val: int, max_val: int) -> int:
    return random.randint(min_val, max_val)


def _rand_float(min_val: float, max_val: float) -> float:
    return random.uniform(min_val, max_val)


def _rand_string(length: int) -> str:
    letters = string.ascii_letters + string.digits
    return ''.join(random.choices(letters, k=length))


def _rand_hex(length: int) -> str:
    return ''.join(random.choices(string.hexdigits[:-6], k=length))


def _rand_password(length: int) -> str:
    charset = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choices(charset, k=length))


def _rand_choice(options: list[str]) -> str:
    return random.choice(options)


def _rand_bool() -> bool:
    return random.choice([True, False])


def generate_values(args) -> list[str]:
    """Generate random values based on parsed args. Returns list of strings."""
    results = []

    if args.int:
        for _ in range(args.count):
            results.append(str(_rand_int(args.min, args.max)))
    elif args.float:
        for _ in range(args.count):
            results.append(f"{_rand_float(args.min, args.max):g}")
    elif args.string:
        for _ in range(args.count):
            results.append(_rand_string(args.length))
    elif args.uuid:
        for _ in range(args.count):
            results.append(str(uuid.uuid4()))
    elif args.hex:
        for _ in range(args.count):
            results.append(_rand_hex(args.length))
    elif args.passwd:
        for _ in range(args.count):
            results.append(_rand_password(args.length))
    elif args.choice:
        options = args.choice.split(',')
        for _ in range(args.count):
            results.append(_rand_choice(options))
    elif args.bool:
        for _ in range(args.count):
            results.append(str(_rand_bool()).lower())
    else:
        # Default: random int
        for _ in range(args.count):
            results.append(str(_rand_int(args.min, args.max)))

    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description='Random data generator — numbers, strings, UUIDs, passwords, and more.',
    )
    parser.add_argument('--int', action='store_true', help='Generate random integer(s)')
    parser.add_argument('--float', action='store_true', help='Generate random float(s)')
    parser.add_argument('--string', action='store_true', help='Generate random string(s)')
    parser.add_argument('--uuid', action='store_true', help='Generate random UUID(s) (v4)')
    parser.add_argument('--hex', action='store_true', help='Generate random hex string(s)')
    parser.add_argument('--pass', dest='passwd', action='store_true', help='Generate random password(s)')
    parser.add_argument('--choice', type=str, metavar='a,b,c', help='Pick random choice from comma-separated list')
    parser.add_argument('--bool', action='store_true', help='Generate random boolean(s)')
    parser.add_argument('--count', '-n', type=int, default=1, help='Number of values to generate (default: 1)')
    parser.add_argument('--min', type=float, default=0, help='Minimum value for numbers (default: 0)')
    parser.add_argument('--max', type=float, default=100, help='Maximum value for numbers (default: 100)')
    parser.add_argument('--len', dest='length', type=int, default=12, help='Length for string/hex/password (default: 12)')
    parser.add_argument('--csv', action='store_true', help='Output as comma-separated values')
    parser.add_argument('--seed', type=int, default=None, help='Seed for reproducible results')

    args = parser.parse_args(argv)

    if args.count < 1:
        print('error: --count/-n must be at least 1', file=sys.stderr)
        return 1

    if args.length < 1:
        print('error: --len must be at least 1', file=sys.stderr)
        return 1

    if args.min > args.max:
        print('error: --min must not be greater than --max', file=sys.stderr)
        return 1

    if args.seed is not None:
        random.seed(args.seed)

    values = generate_values(args)

    if args.csv:
        print(','.join(values))
    else:
        for v in values:
            print(v)

    return 0


if __name__ == '__main__':
    sys.exit(main())
