#!/usr/bin/env python3
"""stopwatch — Terminal stopwatch with lap support.

Usage: stopwatch [--countdown=<seconds>]
       stopwatch --countdown=60

Starts an interactive stopwatch with real-time display.
Press Ctrl+C to stop and see results.
Press Enter during run to record a lap.
Zero-dependency (stdlib only).
"""

import sys, time, select, os

def clear_line():
    sys.stderr.write('\r' + ' ' * 60 + '\r')

def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:05.2f}"
    return f"{m:02d}:{s:05.2f}"

def main():
    args = sys.argv[1:]
    countdown = 0
    for a in args:
        if a.startswith('--countdown='):
            countdown = float(a.split('=', 1)[1])
        elif a == '-h' or a == '--help':
            print(__doc__)
            return

    laps = []
    start = time.time()
    if countdown > 0:
        end_time = start + countdown
        print(f"  Countdown: {format_time(countdown)}", file=sys.stderr)
        print(f"  Press Ctrl+C to stop", file=sys.stderr)
    else:
        print(f"  Stopwatch started. Press Enter for lap, Ctrl+C to stop.", file=sys.stderr)

    last_lap = start
    try:
        while True:
            now = time.time()
            if countdown > 0:
                remaining = end_time - now
                if remaining <= 0:
                    clear_line()
                    print(f"\r  Time's up! ({format_time(0)})     ", file=sys.stderr)
                    break
                display = format_time(remaining)
            else:
                display = format_time(now - start)

            elapsed = now - start
            clear_line()
            sys.stderr.write(f"\r  ⏱  {display}")
            sys.stderr.flush()

            # Check for Enter key (lap)
            if select.select([sys.stdin], [], [], 0.05)[0]:
                line = sys.stdin.readline()
                if countdown > 0:
                    break
                lap_time = time.time() - last_lap
                total_time = time.time() - start
                laps.append((len(laps)+1, lap_time, total_time))
                clear_line()
                print(f"\r  🏁 Lap {len(laps):2d}: {format_time(lap_time)} (total: {format_time(total_time)})", file=sys.stderr)
                last_lap = time.time()

    except KeyboardInterrupt:
        pass

    total = time.time() - start if countdown == 0 else countdown
    print(file=sys.stderr)
    print(file=sys.stderr)
    print(f"  {'='*35}", file=sys.stderr)
    if countdown > 0:
        print(f"  Countdown finished: {format_time(countdown)}", file=sys.stderr)
    else:
        print(f"  Total time: {format_time(total)}", file=sys.stderr)
    if laps:
        print(f"  Laps: {len(laps)}", file=sys.stderr)
        for n, lt, tt in laps:
            print(f"    Lap {n:2d}: {format_time(lt)}", file=sys.stderr)
    print(f"  {'='*35}", file=sys.stderr)

if __name__ == '__main__':
    main()
