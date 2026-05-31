#!/usr/bin/env python3
"""watch — Run command periodically, showing output.

Usage: watch "ls -la"              # every 2 seconds
       watch -n 5 "date"           # every 5 seconds
       watch -d "ps aux"           # highlight differences

Like standard Unix 'watch' command.
Zero-dependency (stdlib only).
"""

import sys
import subprocess
import time
import os


def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')


def main():
    args = sys.argv[1:]
    interval = 2
    highlight = False

    filtered = []
    i = 0
    while i < len(args):
        if args[i] == '-n' and i + 1 < len(args):
            interval = float(args[i + 1])
            i += 2
        elif args[i] == '-d':
            highlight = True
            i += 1
        elif args[i] in ('-h', '--help'):
            print(__doc__)
            return
        else:
            filtered.append(args[i])
            i += 1

    if not filtered:
        print("Usage: watch [-n <seconds>] [-d] <command>")
        return

    cmd = ' '.join(filtered)
    prev_output = ''

    try:
        while True:
            clear_screen()
            now = time.strftime('%Y-%m-%d %H:%M:%S')
            print(f"  Every {interval}s: {cmd}")
            print(f"  {now}")
            print(f"  {'─' * 50}")

            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            output = result.stdout + result.stderr

            if highlight and prev_output:
                output_lines = output.split('\n')
                prev_lines = prev_output.split('\n')
                for idx, line in enumerate(output_lines):
                    if idx < len(prev_lines) and line != prev_lines[idx]:
                        print(f"\033[7m{line}\033[0m")  # inverted
                    else:
                        print(line)
            else:
                print(output)

            prev_output = output
            time.sleep(interval)
    except KeyboardInterrupt:
        pass


# === Auto-registration metadata ===
TOOL_META = {
    "name": "watch",
    "func": "main",
    "desc": 'Run command periodically, showing output',
}

if __name__ == '__main__':
    main()
