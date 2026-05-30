#!/usr/bin/env python3
"""spinner — Show an animated spinner in terminal.

Usage: spinner [--message="Loading..."] [--style=braille|dots|arrows|clock]
       long_running_cmd & spinner --pid=$! --message="Building..."

Shows a configurable spinner animation for long-running tasks.
Zero-dependency (stdlib only).
"""

import sys, time, itertools, threading, os

STYLES = {
    'braille': ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'],
    'dots': ['▁', '▃', '▄', '▅', '▆', '▇', '█', '▇', '▆', '▅', '▄', '▃'],
    'arrows': ['←', '↖', '↑', '↗', '→', '↘', '↓', '↙'],
    'clock': ['🕐', '🕑', '🕒', '🕓', '🕔', '🕕', '🕖', '🕗', '🕘', '🕙', '🕚', '🕛'],
    'pulse': ['█', '▓', '▒', '░', '▒', '▓'],
    'moon': ['🌑', '🌒', '🌓', '🌔', '🌕', '🌖', '🌗', '🌘'],
}

def spin(message, style='braille', delay=0.1, pid=None):
    """Display spinner until process finishes or Ctrl+C."""
    frames = STYLES.get(style, STYLES['braille'])
    try:
        while True:
            for frame in frames:
                sys.stderr.write(f'\r  {frame} {message}')
                sys.stderr.flush()
                if pid is not None:
                    try:
                        os.kill(pid, 0)
                    except:
                        sys.stderr.write(f'\r  ✓ {message} [done]\n')
                        sys.stderr.flush()
                        return
                time.sleep(delay)
    except KeyboardInterrupt:
        sys.stderr.write(f'\r  ✗ {message} [cancelled]\n')
        sys.stderr.flush()

def main():
    import os
    args = sys.argv[1:]
    if not args or '-h' in args or '--help' in args:
        print(__doc__)
        return

    message = 'Working...'
    style = 'braille'
    delay = 0.1
    pid = None
    count = 0

    for a in args:
        if a.startswith('--message='):
            message = a.split('=', 1)[1]
        elif a.startswith('--style='):
            style = a.split('=', 1)[1]
        elif a.startswith('--delay='):
            delay = float(a.split('=', 1)[1])
        elif a.startswith('--pid='):
            pid = int(a.split('=', 1)[1])
        elif a.startswith('--count='):
            count = int(a.split('=', 1)[1])

    if pid is not None:
        spin(message, style, delay, pid)
    elif count > 0:
        frames = STYLES.get(style, STYLES['braille'])
        for i in range(count):
            frame = frames[i % len(frames)]
            sys.stderr.write(f'\r  {frame} {message} [{i+1}/{count}]')
            sys.stderr.flush()
            time.sleep(delay)
        sys.stderr.write(f'\r  ✓ {message} [done]\n')
    else:
        spin(message, style, delay)

if __name__ == '__main__':
    main()
