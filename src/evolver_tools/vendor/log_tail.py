#!/usr/bin/env python3
"""log-tail — Tail log files with follow, filter, and colorize.

Usage: log-tail <file> [--lines=20] [--follow] [--filter=<pattern>]
       log-tail system.log --follow --lines=10
       tail -f app.log | log-tail --colorize

Tails log files with optional follow mode (like tail -f).
Supports grep filtering, line count, and basic log level colorization.
Zero-dependency (stdlib only).
"""

import sys, os, time, re

# Basic log level colors
LEVEL_COLORS = {
    'ERROR': '\033[1;31m',   # Bold Red
    'WARN': '\033[1;33m',    # Bold Yellow  
    'INFO': '\033[1;32m',    # Bold Green
    'DEBUG': '\033[1;34m',   # Bold Blue
    'TRACE': '\033[1;35m',   # Bold Purple
    'FATAL': '\033[1;37;41m', # White on Red
}
RESET = '\033[0m'

def colorize_line(line):
    """Add ANSI color based on log level."""
    for level, color in LEVEL_COLORS.items():
        if level in line.upper() or f'[{level}]' in line or f'|{level}|' in line:
            return f"{color}{line}{RESET}"
    return line

def tail_file(filepath, lines=10, follow=False, filter_pat=None, colorize=False):
    """Tail a file like tail -f."""
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    with open(filepath, 'r') as f:
        # Go to end
        f.seek(0, 2)
        file_size = f.tell()
        
        # Read last N lines
        if lines > 0:
            f.seek(0)
            all_lines = f.readlines()
            tail_lines = all_lines[-lines:]
            for line in tail_lines:
                line = line.rstrip('\n\r')
                if filter_pat and not re.search(filter_pat, line):
                    continue
                if colorize:
                    line = colorize_line(line)
                print(line)
        
        if follow:
            f.seek(file_size)
            try:
                while True:
                    line = f.readline()
                    if line:
                        line = line.rstrip('\n\r')
                        if filter_pat and not re.search(filter_pat, line):
                            continue
                        if colorize:
                            line = colorize_line(line)
                        print(line)
                    else:
                        time.sleep(0.1)
            except KeyboardInterrupt:
                pass

def main():
    args = sys.argv[1:]
    if not args or '-h' in args or '--help' in args:
        print(__doc__)
        return

    lines = 10
    follow = False
    filter_pat = None
    colorize = False
    files = []

    for a in args:
        if a.startswith('--lines='):
            lines = int(a.split('=', 1)[1])
        elif a == '--follow' or a == '-f':
            follow = True
        elif a.startswith('--filter='):
            filter_pat = a.split('=', 1)[1]
        elif a == '--colorize':
            colorize = True
        elif not a.startswith('-'):
            files.append(a)

    if not files:
        # Pipe mode
        stdin_lines = sys.stdin.readlines()
        tail = stdin_lines[-lines:]
        for line in tail:
            line = line.rstrip('\n\r')
            if filter_pat and not re.search(filter_pat, line):
                continue
            if colorize:
                line = colorize_line(line)
            print(line)
        return

    for f in files:
        if len(files) > 1:
            print(f"==> {f} <==")
        tail_file(f, lines=lines, follow=follow, filter_pat=filter_pat, colorize=colorize)


# === Auto-registration metadata ===
TOOL_META = {
    "name": "log-tail",
    "func": "main",
    "desc": 'Tail logs with follow, filter, colorize',
}

if __name__ == '__main__':
    main()
