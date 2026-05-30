#!/usr/bin/env python3
"""reminder — Set a timer-based reminder.

Usage: reminder <message> --in=<seconds>
       reminder "Take a break" --in=300
       reminder "Meeting in 5 min" --in=5m  (supports m/h suffixes)

Alerts with a terminal bell (\\a) when time is up.
Zero-dependency (stdlib only).
"""

import sys, time, re

def parse_duration(s):
    """Parse duration string like 300, 5m, 2h into seconds."""
    s = s.strip().lower()
    if s.endswith('h'):
        return float(s[:-1]) * 3600
    if s.endswith('m'):
        return float(s[:-1]) * 60
    if s.endswith('s'):
        return float(s[:-1])
    return float(s)

def format_remaining(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    parts = []
    if h > 0:
        parts.append(f"{h}h")
    if m > 0:
        parts.append(f"{m}m")
    if s > 0 or not parts:
        parts.append(f"{s}s")
    return ' '.join(parts)

def main():
    args = sys.argv[1:]
    if not args or '-h' in args or '--help' in args:
        print(__doc__)
        return

    duration = 0
    message_parts = []

    for a in args:
        if a.startswith('--in='):
            duration = parse_duration(a.split('=', 1)[1])
        elif not a.startswith('-'):
            message_parts.append(a)

    if duration <= 0:
        print("Usage: reminder <message> --in=<seconds|5m|2h>")
        return

    message = ' '.join(message_parts) if message_parts else "Time's up!"
    end_time = time.time() + duration

    print(f"  Reminder set: \"{message}\"")
    print(f"  In: {format_remaining(duration)}")
    print(f"  At: {time.strftime('%H:%M:%S', time.localtime(end_time))}")
    print()

    try:
        while True:
            remaining = end_time - time.time()
            if remaining <= 0:
                break
            if remaining < 10:
                sys.stderr.write(f"\r  ⏰ {remaining:.0f}s  ")
                sys.stderr.flush()
                time.sleep(0.2)
            else:
                # Show countdown every 5 seconds for long timers
                sys.stderr.write(f"\r  ⏰ {format_remaining(remaining)} remaining  ")
                sys.stderr.flush()
                time.sleep(5)
    except KeyboardInterrupt:
        print(file=sys.stderr)
        print("  Reminder cancelled.", file=sys.stderr)
        return

    # Alert!
    print(file=sys.stderr)
    print('\a')  # Bell
    print()
    print(f"  {'='*40}")
    print(f"  ⏰ REMINDER: {message}")
    print(f"  {'='*40}")
    print('\a')  # Another bell


# === Auto-registration metadata ===
TOOL_META = {
    "name": "reminder",
    "func": "main",
    "desc": 'Timer-based reminder with countdown',
}

if __name__ == '__main__':
    main()
