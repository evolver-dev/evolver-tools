#!/usr/bin/env python3
"""Zero-dependency CLI dice roller (d4, d6, d8, d10, d12, d20, d100)."""

import argparse
import random
import sys

TOOL_META = {
    'name': 'dice-roll',
    'func': 'main',
    'desc': 'Dice roller (d4, d6, d8, d10, d12, d20, d100)',
}


def parse_dice_spec(spec: str) -> tuple[int, int]:
    """Parse a dice spec like '2d6' into (count, sides).

    Raises ValueError on invalid format or unsupported die type.
    """
    if 'd' not in spec:
        raise ValueError(f"Invalid dice spec '{spec}': missing 'd' (e.g. 2d6)")

    parts = spec.split('d', maxsplit=1)
    count_str, sides_str = parts

    if not sides_str:
        raise ValueError(f"Invalid dice spec '{spec}': no sides after 'd'")

    count = int(count_str) if count_str else 1
    sides = int(sides_str)

    valid_sides = {4, 6, 8, 10, 12, 20, 100}
    if sides not in valid_sides:
        raise ValueError(
            f"Unsupported die type d{sides}. Supported: d4, d6, d8, d10, d12, d20, d100"
        )

    if count < 1:
        raise ValueError(f"Number of dice must be at least 1, got {count}")

    return count, sides


def roll_dice(count: int, sides: int) -> list[int]:
    """Roll `count` dice with `sides` sides, returning a list of results."""
    return [random.randint(1, sides) for _ in range(count)]


def format_results(results: list[int], sides: int) -> str:
    """Format a roll result as a human-readable string."""
    total = sum(results)
    parts = ', '.join(str(r) for r in results)
    label = f"d{sides}"
    return f"{label}: [{parts}] = {total}"


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Parse args, roll dice, print results."""
    parser = argparse.ArgumentParser(
        description='Dice roller — roll any supported die type.',
    )
    parser.add_argument(
        '--dice',
        type=str,
        default='1d6',
        help='Dice to roll, e.g. 2d6, 1d20, 3d10 (default: 1d6)',
    )
    parser.add_argument(
        '--rolls',
        type=int,
        default=1,
        help='Number of times to roll (default: 1)',
    )

    args = parser.parse_args(argv)

    if args.rolls < 1:
        print(f"error: --rolls must be at least 1, got {args.rolls}", file=sys.stderr)
        return 1

    try:
        count, sides = parse_dice_spec(args.dice)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    for i in range(args.rolls):
        results = roll_dice(count, sides)
        line = format_results(results, sides)
        if args.rolls > 1:
            print(f"Roll #{i + 1}:  {line}")
        else:
            print(line)

    return 0


if __name__ == '__main__':
    sys.exit(main())
