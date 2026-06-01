#!/usr/bin/env python3
"""humanize — Convert raw numbers to human-readable format.

Usage: humanize 1048576
       humanize --size 1048576
       humanize --duration 3661
       humanize --number 1500000

Modes (auto-detect or explicit):
  --size / -s      Bytes → KB, MB, GB, TB (binary 1024; --si for decimal 1000)
  --duration / -d  Seconds → 1h 1m 1s, 1 day 2h, etc.
  --number / -n    Plain number → 1.5M, 2.5K, 0.0015 → 1.5ms, etc.

Accepts stdin, single positional arg, or explicit flag + value.
"""

import sys
import os


def human_size(value, si=False):
    """Format bytes as human-readable."""
    base = 1000 if si else 1024
    units = ["B", "KB", "MB", "GB", "TB", "PB", "EB"]
    if value < base:
        return f"{value:.0f} {units[0]}"
    for i, unit in enumerate(units[1:], start=1):
        if value < base ** (i + 1):
            val = value / (base ** i)
            # Trim trailing zeros but keep at least 2 significant digits
            s = f"{val:.2f}".rstrip("0").rstrip(".")
            return f"{s} {unit}"
    # Beyond largest unit
    val = value / (base ** (len(units) - 1))
    s = f"{val:.2f}".rstrip("0").rstrip(".")
    return f"{s} {units[-1]}"


def human_duration(seconds):
    """Format seconds as human-readable duration."""
    seconds = int(seconds)
    parts = []

    days, seconds = divmod(abs(seconds), 86400)
    hours, seconds = divmod(seconds, 3600)
    mins, secs = divmod(seconds, 60)

    if days > 0:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{hours}h")
    if mins > 0:
        parts.append(f"{mins}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")

    return " ".join(parts)


def human_number(value):
    """Format a number with metric suffixes (K, M, B, T, ms, µs, ns)."""
    abs_val = abs(value)

    # Small numbers → sub-unit suffixes
    if abs_val < 1 and abs_val > 0:
        if abs_val >= 0.1:
            return f"{value:.3f}".rstrip("0").rstrip(".")
        if abs_val >= 0.01:
            return f"{value:.4f}".rstrip("0").rstrip(".")
        # Use metric prefixes for very small numbers
        for factor, suffix in [(1e-3, "ms"), (1e-6, "µs"), (1e-9, "ns"), (1e-12, "ps")]:
            if abs_val >= factor:
                val = value / factor
                s = f"{val:.2f}".rstrip("0").rstrip(".")
                return f"{s}{suffix}"
        # Below pico — use scientific notation
        return f"{value:.2e}"

    # Large numbers → metric suffixes
    for factor, suffix in [(1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")]:
        if abs_val >= factor:
            val = value / factor
            s = f"{val:.2f}".rstrip("0").rstrip(".")
            return f"{s}{suffix}"

    # In the 1–999 range, just format nicely
    s = f"{value:.2f}".rstrip("0").rstrip(".")
    return s


def parse_arg(value):
    """Parse a string to int if whole, else float."""
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return None


def detect_mode(value):
    """Auto-detect mode for a bare number.

    Integers >= 1024 → size (bytes), everything else → number.
    """
    if isinstance(value, int) and value >= 1024:
        return "size"
    return "number"


def main():
    args = sys.argv[1:]

    # Help
    if not args or "-h" in args or "--help" in args:
        print(__doc__.strip())
        return

    mode = None
    value = None
    si = False

    # Parse flags and value
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("--size", "-s"):
            mode = "size"
            i += 1
        elif arg in ("--duration", "-d"):
            mode = "duration"
            i += 1
        elif arg in ("--number", "-n"):
            mode = "number"
            i += 1
        elif arg == "--si":
            si = True
            i += 1
        else:
            if value is not None:
                print(f"Error: unexpected argument '{arg}'", file=sys.stderr)
                sys.exit(1)
            parsed = parse_arg(arg)
            if parsed is None:
                print(f"Error: cannot parse '{arg}' as number", file=sys.stderr)
                sys.exit(1)
            value = parsed
            i += 1

    # If no value yet, try stdin
    if value is None:
        if not sys.stdin.isatty():
            raw = sys.stdin.read()
            raw = raw.strip() if raw else ""
            if raw:
                parsed = parse_arg(raw)
                if parsed is not None:
                    value = parsed
        if value is None:
            print("Error: no number provided", file=sys.stderr)
            print(__doc__.strip())
            sys.exit(1)

    # Auto-detect mode if not specified
    if mode is None:
        mode = detect_mode(value)

    # Dispatch
    if mode == "size":
        print(human_size(value, si=si))
    elif mode == "duration":
        print(human_duration(value))
    elif mode == "number":
        print(human_number(value))


# === Auto-registration metadata ===
TOOL_META = {
    "name": "humanize",
    "func": "main",
    "desc": "Convert raw numbers to human-readable format (size, duration, count)",
}

if __name__ == "__main__":
    main()
