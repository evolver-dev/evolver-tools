#!/usr/bin/env python3
"""timer — 终端计时器 / Terminal countdown timer & stopwatch.

Zero-dependency CLI timer with countdown, stopwatch, and alarm modes.
"""

import sys
import os
import time
import argparse
import itertools


def entry():
    args = parse_args()

    if args.stopwatch:
        run_stopwatch()
    elif args.countdown:
        run_countdown(parse_duration(args.countdown))
    elif args.countdown_from:
        run_countdown(args.countdown_from)
    else:
        # Default: show help
        print("Use --stopwatch, --countdown <time>, or --timer <seconds>")
        sys.exit(0)


def format_time(seconds: float) -> str:
    """Format seconds as HH:MM:SS or MM:SS."""
    mins, secs = divmod(int(seconds), 60)
    hours, mins = divmod(mins, 60)
    if hours > 0:
        return f"{hours:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


def parse_duration(s: str) -> int:
    """Parse duration like '90', '1m30s', '2h' to seconds."""
    s = s.strip().lower()
    if s.isdigit():
        return int(s)

    total = 0
    num = ""
    for ch in s:
        if ch.isdigit() or ch == ".":
            num += ch
        else:
            if num:
                val = float(num)
                if ch == "h":
                    total += int(val * 3600)
                elif ch == "m":
                    total += int(val * 60)
                elif ch == "s":
                    total += int(val)
                num = ""
    if num:
        total += int(num)
    return max(total, 1)


def run_stopwatch():
    """Run an interactive stopwatch."""
    print("Stopwatch started. Press Ctrl+C to stop.")
    print()
    start = time.time()
    try:
        for _ in itertools.count():
            elapsed = time.time() - start
            print(f"\r  {format_time(elapsed)}", end="", flush=True)
            time.sleep(0.1)
    except KeyboardInterrupt:
        elapsed = time.time() - start
        print(f"\n\n  Stopped at {format_time(elapsed)}")
        print(f"  ({elapsed:.1f} seconds)")


def run_countdown(seconds: int):
    """Run a countdown timer."""
    print(f"Countdown: {format_time(seconds)}")
    print()
    try:
        remaining = seconds
        while remaining > 0:
            print(f"\r  {format_time(remaining)}", end="", flush=True)
            time.sleep(1)
            remaining -= 1
        print(f"\r  00:00")
        print()
        # Alarm notification
        bell = "\a" * 3
        print(f"{bell}  TIME'S UP! ({format_time(seconds)})")
        # Keep beeping for a bit
        for _ in range(5):
            print("\a", end="", flush=True)
            time.sleep(0.5)
    except KeyboardInterrupt:
        elapsed = seconds - (remaining if 'remaining' in dir() else seconds)
        print(f"\n\n  Stopped at {format_time(elapsed)}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="timer — 终端计时器 / Terminal timer & stopwatch",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  timer --stopwatch                 # Start stopwatch
  timer --countdown 90              # Countdown 90 seconds
  timer --countdown 5m              # Countdown 5 minutes
  timer --countdown 1h30m           # Countdown 1 hour 30 minutes
  timer -t 300                      # Countdown 300 seconds
""")
    parser.add_argument("-s", "--stopwatch", action="store_true",
                        help="Start stopwatch mode")
    parser.add_argument("-c", "--countdown", type=str, nargs="?", const="60",
                        metavar="DURATION",
                        help="Countdown timer (default: 60s). Format: 90, 5m, 1h30m")
    parser.add_argument("-t", "--timer", dest="countdown_from", type=int,
                        metavar="SECONDS",
                        help="Countdown from N seconds")
    return parser.parse_args()



# === Auto-registration metadata ===
TOOL_META = {
    "name": "timer",
    "func": "entry",
    "desc": 'Countdown timer and stopwatch',
}

if __name__ == "__main__":
    entry()
