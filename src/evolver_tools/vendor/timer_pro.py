#!/usr/bin/env python3
"""timer-pro — Countdown timer, stopwatch, and alarm.

Usage:
  timer-pro 5m          — countdown 5 minutes
  timer-pro 1h30m       — countdown 1h 30m
  timer-pro stopwatch   — start stopwatch (Ctrl+C to stop)
  timer-pro 10s --bell  — countdown + bell at end

Time format: 30s, 5m, 1h, 1h30m, 1h30m15s
Zero-dependency (stdlib only).
"""
import sys, time, re

def parse_duration(s):
    total = 0
    for m in re.finditer(r'(\d+)([hms])', s):
        n = int(m.group(1))
        unit = m.group(2)
        if unit == 'h': total += n * 3600
        elif unit == 'm': total += n * 60
        elif unit == 's': total += n
    return total

def format_time(secs):
    h = secs // 3600
    m = (secs % 3600) // 60
    s = secs % 60
    if h: return f"{h}h{m:02d}m{s:02d}s"
    if m: return f"{m:02d}m{s:02d}s"
    return f"{s:02d}s"

def countdown(secs, bell):
    try:
        while secs > 0:
            print(f"\r  {format_time(secs)}  ", end='', flush=True)
            time.sleep(1)
            secs -= 1
        print(f"\r  {'DONE!' :^10}  ")
        if bell:
            for _ in range(3):
                print('\a', end='', flush=True)
                time.sleep(0.5)
    except KeyboardInterrupt:
        print("\r  cancelled  ")

def stopwatch():
    start = time.time()
    try:
        while True:
            elapsed = time.time() - start
            print(f"\r  {format_time(int(elapsed))}  ", end='', flush=True)
            time.sleep(0.1)
    except KeyboardInterrupt:
        elapsed = time.time() - start
        print(f"\r  Final: {format_time(int(elapsed))}  ")

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__.strip())
        return
    
    bell = '--bell' in args
    if bell:
        args.remove('--bell')
    
    cmd = args[0]
    if cmd == 'stopwatch':
        stopwatch()
        return
    
    secs = parse_duration(cmd)
    if secs > 0:
        countdown(secs, bell)
    else:
        print(f"Unknown duration: {cmd}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
