#!/usr/bin/env python3
"""hexdec — Convert between hex, decimal, octal, binary.

Usage: hexdec ff
       hexdec 255
       hexdec 0xff
       hexdec 0o377
       hexdec 0b11111111
       hexdec --in hex --out dec ff
       hexdec --in hex --out all ff
       hexdec --batch ff 255 0o377
       echo ff | hexdec
       echo 255 | hexdec

Auto-detects input format: 0x prefix → hex, 0o → octal, 0b → binary, else decimal.
Omitting --out shows all 4 representations.
Specify --out dec/hex/oct/bin/all to pick output format.
"""

import sys

TOOL_META = {
    "name": "hexdec",
    "func": "main",
    "desc": "Convert between hex, decimal, octal, binary",
}


def parse_value(s, fmt=None):
    """Parse a string into an integer. If fmt is None, auto-detect."""
    s = s.strip()
    if fmt is None:
        if s.startswith("0x") or s.startswith("0X"):
            return int(s, 16)
        elif s.startswith("0o") or s.startswith("0O"):
            return int(s, 8)
        elif s.startswith("0b") or s.startswith("0B"):
            return int(s, 2)
        else:
            return int(s, 10)
    elif fmt == "hex":
        return int(s, 16)
    elif fmt == "dec":
        return int(s, 10)
    elif fmt == "oct":
        return int(s, 8)
    elif fmt == "bin":
        return int(s, 2)
    else:
        raise ValueError(f"Unknown input format: {fmt}")


def fmt_dec(n):
    return str(n)


def fmt_hex(n):
    return hex(n)


def fmt_oct(n):
    return oct(n)


def fmt_bin(n):
    return bin(n)


_FORMATTERS = {
    "dec": ("Decimal", fmt_dec),
    "hex": ("Hex", fmt_hex),
    "oct": ("Octal", fmt_oct),
    "bin": ("Binary", fmt_bin),
}

_OUTPUT_ORDER = ["hex", "dec", "oct", "bin"]


def format_line(n, out_fmt):
    """Format a single integer according to the output format."""
    if out_fmt == "all":
        parts = []
        for key in _OUTPUT_ORDER:
            label, formatter = _FORMATTERS[key]
            parts.append(f"{label:<8}{formatter(n)}")
        return "  ".join(parts)
    elif out_fmt in _FORMATTERS:
        label, formatter = _FORMATTERS[out_fmt]
        return f"{label:<8}{formatter(n)}"
    else:
        raise ValueError(f"Unknown output format: {out_fmt}")


def print_header(out_fmt):
    """Print a column header for --batch mode with --out all."""
    if out_fmt == "all":
        parts = []
        for key in _OUTPUT_ORDER:
            label, _ = _FORMATTERS[key]
            parts.append(f"{label:<8}{label}")
        print("  ".join(parts))
        print("  " + "-" * (len(parts) * 14))


def main():
    args = sys.argv[1:]

    if "-h" in args or "--help" in args:
        print(__doc__)
        return

    # Parse options
    in_fmt = None
    out_fmt = "all"
    batch_mode = False
    value_args = []

    i = 0
    while i < len(args):
        a = args[i]
        if a in ("--in", "-i"):
            i += 1
            if i < len(args):
                in_fmt = args[i]
        elif a in ("--out", "-o"):
            i += 1
            if i < len(args):
                out_fmt = args[i]
        elif a == "--batch":
            batch_mode = True
        elif a.startswith("-"):
            print(f"Unknown option: {a}", file=sys.stderr)
            sys.exit(1)
        else:
            value_args.append(a)
        i += 1

    # Read from stdin if no arguments
    if not value_args:
        raw = sys.stdin.read().strip()
        if raw:
            value_args = raw.splitlines()

    if not value_args:
        print(__doc__)
        return

    if batch_mode:
        print_header(out_fmt)

    for val in value_args:
        val = val.strip()
        if not val:
            continue
        try:
            n = parse_value(val, in_fmt)
            print(format_line(n, out_fmt))
        except ValueError as e:
            print(f"Error: cannot parse '{val}': {e}", file=sys.stderr)
            if not batch_mode:
                sys.exit(1)
