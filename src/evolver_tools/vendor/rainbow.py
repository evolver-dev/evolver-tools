#!/usr/bin/env python3
"""rainbow — Display text in rainbow colors.

Usage: rainbow "Hello World!"
       echo "colorful text" | rainbow [--bold]

Prints text cycling through rainbow gradient. Piped input supported.
Zero-dependency (stdlib only).
"""

import sys, math

RAINBOW_COLORS = [
    (255, 0, 0),     # Red
    (255, 127, 0),   # Orange
    (255, 255, 0),   # Yellow
    (0, 255, 0),     # Green
    (0, 0, 255),     # Blue
    (75, 0, 130),    # Indigo
    (148, 0, 211),   # Violet
]

def rgb_to_ansi(r, g, b):
    return f'\033[38;2;{r};{g};{b}m'

def get_rainbow_color(index, total_len, spread=1.0):
    if total_len <= 1:
        return RAINBOW_COLORS[0]
    pos = (index / total_len) * (len(RAINBOW_COLORS) - 1) * spread
    idx1 = int(pos) % len(RAINBOW_COLORS)
    idx2 = (idx1 + 1) % len(RAINBOW_COLORS)
    frac = pos - int(pos)
    r1, g1, b1 = RAINBOW_COLORS[idx1]
    r2, g2, b2 = RAINBOW_COLORS[idx2]
    return (
        int(r1 + (r2 - r1) * frac),
        int(g1 + (g2 - g1) * frac),
        int(b1 + (b2 - b1) * frac),
    )

def main():
    args = sys.argv[1:]
    bold = '--bold' in args
    reset = '\033[0m'

    text_args = [a for a in args if not a.startswith('-')]
    if text_args:
        text = ' '.join(text_args)
    elif not sys.stdin.isatty():
        text = sys.stdin.read().strip()
    else:
        print("Usage: rainbow <text>")
        print("       echo 'Hello' | rainbow")
        return

    if not text:
        return

    lines = text.splitlines()
    for line in lines:
        result = []
        for i, ch in enumerate(line):
            if ch.strip():
                r, g, b = get_rainbow_color(i, len(line))
                result.append(f'{rgb_to_ansi(r, g, b)}{ch}')
            else:
                result.append(ch)
        result.append(reset)
        print(''.join(result))


# === Auto-registration metadata ===
TOOL_META = {
    "name": "rainbow",
    "func": "main",
    "desc": 'Rainbow-colored text output',
}

if __name__ == '__main__':
    main()
