#!/usr/bin/env python3
"""pomodoro — Pomodoro timer for productivity.

Usage: pomodoro                     # 25min work + 5min break
       pomodoro -w 30 -b 10         # custom work/break
       pomodoro -n 4                # 4 cycles

Uses terminal bell for alerts.
Zero-dependency (stdlib only).
"""

import sys
import time


def timer(minutes, label, sound=True):
    total = int(minutes * 60)
    bar_width = 30
    for remaining in range(total, 0, -1):
        elapsed = total - remaining
        progress = int(elapsed / total * bar_width) if total > 0 else 0
        bar = '█' * progress + '░' * (bar_width - progress)
        mins = remaining // 60
        secs = remaining % 60
        print(f'\r  {label}: [{bar}] {mins:02d}:{secs:02d} ', end='', flush=True)
        time.sleep(1)
    print()
    if sound:
        for _ in range(3):
            sys.stdout.write('\a')
            sys.stdout.flush()
            time.sleep(0.3)


def main():
    args = sys.argv[1:]
    work_min = 25
    break_min = 5
    cycles = 1
    long_break = 15

    i = 0
    while i < len(args):
        if args[i] == '-w' and i + 1 < len(args):
            work_min = int(args[i + 1])
            i += 2
        elif args[i] == '-b' and i + 1 < len(args):
            break_min = int(args[i + 1])
            i += 2
        elif args[i] == '-l' and i + 1 < len(args):
            long_break = int(args[i + 1])
            i += 2
        elif args[i] == '-n' and i + 1 < len(args):
            cycles = int(args[i + 1])
            i += 2
        elif args[i] in ('-h', '--help'):
            print(__doc__)
            return
        else:
            i += 1

    print(f"  Pomodoro: {cycles} cycles ({work_min}min work / {break_min}min break)")
    print(f"  {('=' * 40)}")
    
    try:
        for c in range(1, cycles + 1):
            print(f"\n  Cycle {c}/{cycles}")
            timer(work_min, f'Work {c}/{cycles}')
            if c < cycles:
                is_long = (c % 4 == 0)
                break_dur = long_break if is_long else break_min
                label = f'Break {c}/{cycles}' + (' (long)' if is_long else '')
                print(f"  Rest time ({break_dur}min)...")
                timer(break_dur, label)
            else:
                print(f"\n  ✅ All {cycles} cycles complete!")
                print(f"  Total: {work_min * cycles}min work + {break_min * (cycles - 1)}min break")
    except KeyboardInterrupt:
        print(f"\n  ⏹  Interrupted")


# === Auto-registration metadata ===
TOOL_META = {
    "name": "pomodoro",
    "func": "main",
    "desc": 'Pomodoro timer (work/break cycles)',
}

if __name__ == '__main__':
    main()
