#!/usr/bin/env python3
"""colorize — Terminal text colorizer with foreground/background colors and text styles."""
import sys
import os
import argparse

_STYLES = {
    "bold": ("\033[1m", "\033[22m"),
    "dim": ("\033[2m", "\033[22m"),
    "italic": ("\033[3m", "\033[23m"),
    "underline": ("\033[4m", "\033[24m"),
    "blink": ("\033[5m", "\033[25m"),
    "strikethrough": ("\033[9m", "\033[29m"),
}

_NAMED_COLORS = {
    "black": "0",
    "red": "1",
    "green": "2",
    "yellow": "3",
    "blue": "4",
    "magenta": "5",
    "cyan": "6",
    "white": "7",
}

_FG_BASE = 30
_BG_BASE = 40
_BRIGHT_OFFSET = 60


def parse_color(color_str, is_background=False):
    """Parse a color string into an ANSI escape code."""
    if not color_str:
        return ""
    base = _BG_BASE if is_background else _FG_BASE
    if color_str.startswith("#"):
        hex_str = color_str.lstrip("#")
        if len(hex_str) == 3:
            hex_str = "".join(c * 2 for c in hex_str)
        if len(hex_str) != 6:
            raise ValueError(f"Invalid hex color: {color_str}")
        r = int(hex_str[0:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:6], 16)
        return f"\033[{base + 8};2;{r};{g};{b}m"
    else:
        clr = color_str.lower()
        if clr.startswith("bright-") or clr.startswith("light-"):
            parts = clr.split("-", 1)
            base_name = parts[1]
            if base_name in _NAMED_COLORS:
                code = int(_NAMED_COLORS[base_name]) + base + _BRIGHT_OFFSET
                return f"\033[{code}m"
            raise ValueError(f"Unknown color: {color_str}")
        if clr in _NAMED_COLORS:
            code = int(_NAMED_COLORS[clr]) + base
            return f"\033[{code}m"
        raise ValueError(f"Unknown color: {color_str}")


def reset_code():
    return "\033[0m"


def apply_style(text, styles, fg_code, bg_code):
    """Apply ANSI codes to text."""
    prefix = reset_code()
    if bg_code:
        prefix += bg_code
    if fg_code:
        prefix += fg_code
    for style_name in styles:
        if style_name in _STYLES:
            prefix += _STYLES[style_name][0]
    suffix = reset_code()
    # Handle line-by-line to preserve styling across lines
    lines = text.split("\n")
    styled_lines = [prefix + line + suffix for line in lines]
    return "\n".join(styled_lines)


def strip_ansi(text):
    """Remove all ANSI escape sequences from text."""
    import re
    ansi_pattern = re.compile(r'\033\[[0-9;]*m')
    return ansi_pattern.sub('', text)


def list_colors():
    """Print a demo of all named colors and styles."""
    print("Named colors:")
    for name in ["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"]:
        fg = parse_color(name)
        bg = parse_color(name, is_background=True)
        bright_name = f"bright-{name}"
        bright_fg = parse_color(bright_name)
        bright_bg = parse_color(bright_name, is_background=True)
        sample = f"{name:<12}"
        bright_sample = f"{bright_name:<12}"
        print(f"  {fg}{sample}{reset_code()}  {bg}{sample}{reset_code()}  {bright_fg}{bright_sample}{reset_code()}  {bright_bg}{bright_sample}{reset_code()}")

    print("\nStyles:")
    for style_name in _STYLES:
        code = _STYLES[style_name][0]
        print(f"  {code}{style_name:<15}{reset_code()}")


def main():
    parser = argparse.ArgumentParser(
        description="Terminal text colorizer. Apply colors and styles to text."
    )
    parser.add_argument("text", nargs="*", help="Text to colorize (if not piped via stdin)")
    parser.add_argument("-c", "--color", default="", help="Foreground color: named or #hex")
    parser.add_argument("-b", "--background", default="", help="Background color: named or #hex")
    parser.add_argument("-s", "--style", action="append", dest="styles", default=[],
                        choices=list(_STYLES.keys()),
                        help="Text style (can be used multiple times)")
    parser.add_argument("--bold", action="store_true", help="Bold text")
    parser.add_argument("--dim", action="store_true", help="Dim text")
    parser.add_argument("--italic", action="store_true", help="Italic text")
    parser.add_argument("--underline", action="store_true", help="Underline text")
    parser.add_argument("--blink", action="store_true", help="Blinking text")
    parser.add_argument("--strikethrough", action="store_true", help="Strikethrough text")
    parser.add_argument("--list", action="store_true", help="List available colors and styles")
    parser.add_argument("--strip", action="store_true", help="Strip ANSI codes from input")
    parser.add_argument("--no-newline", "-n", action="store_true", help="Omit trailing newline")

    args = parser.parse_args()

    if args.list:
        list_colors()
        return

    # Collect text
    text = " ".join(args.text) if args.text else ""
    if not text and not sys.stdin.isatty():
        try:
            text = sys.stdin.read()
        except KeyboardInterrupt:
            text = ""

    if not text:
        # Read from stdin without tty check fallback
        if not sys.stdin.isatty():
            text = sys.stdin.read()
        else:
            print("No input text provided. Pipe text or pass as arguments.", file=sys.stderr)
            sys.exit(1)

    # Collect styles from both --style and individual flags
    styles = list(args.styles)
    style_flags = {
        "bold": args.bold,
        "dim": args.dim,
        "italic": args.italic,
        "underline": args.underline,
        "blink": args.blink,
        "strikethrough": args.strikethrough,
    }
    for sname, enabled in style_flags.items():
        if enabled and sname not in styles:
            styles.append(sname)

    # Strip mode
    if args.strip:
        text = strip_ansi(text)
        if args.no_newline:
            print(text, end="")
        else:
            print(text)
        return

    # Parse colors
    try:
        fg_code = parse_color(args.color) if args.color else ""
        bg_code = parse_color(args.background, is_background=True) if args.background else ""
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    result = apply_style(text.rstrip("\n"), styles, fg_code, bg_code)

    if args.no_newline:
        print(result, end="")
    else:
        print(result)



# === Auto-registration metadata ===
TOOL_META = {
    "name": "colorize",
    "func": "main",
    "desc": 'Terminal text colorizer',
}

if __name__ == "__main__":
    main()
