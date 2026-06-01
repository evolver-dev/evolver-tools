#!/usr/bin/env python3
"""timeout — Run command with timeout limit.

Usage: timeout <seconds> <command> [args...]
       timeout -s KILL 5 ping google.com

Runs a command and kills it if it exceeds the time limit.
Zero-dependency (stdlib only).
"""

import sys
import subprocess
import signal
import time


def main():
    args = sys.argv[1:]
    if not args or '-h' in args or '--help' in args:
        print(__doc__)
        return

    kill_signal = signal.SIGTERM
    if args[0] == '-s' and len(args) > 1:
        sig_name = args[1].upper()
        kill_signal = getattr(signal, f'SIG{sig_name}', signal.SIGTERM)
        args = args[2:]
    elif args[0].startswith('-s') and len(args[0]) > 2:
        sig_name = args[0][2:].upper()
        kill_signal = getattr(signal, f'SIG{sig_name}', signal.SIGTERM)
        args = args[1:]

    if len(args) < 2:
        print("Usage: timeout <seconds> <command> [args...]")
        sys.exit(1)

    try:
        limit = float(args[0])
    except ValueError:
        print(f"Error: invalid timeout: {args[0]}", file=sys.stderr)
        sys.exit(1)

    cmd = args[1:]

    proc = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr)
    start = time.time()

    try:
        proc.wait(timeout=limit)
    except subprocess.TimeoutExpired:
        proc.send_signal(kill_signal)
        elapsed = time.time() - start
        print(f"\n[timeout: command timed out after {elapsed:.1f}s]", file=sys.stderr)
        sys.exit(124)
    except KeyboardInterrupt:
        proc.send_signal(signal.SIGTERM)
        sys.exit(1)


# === Auto-registration metadata ===
TOOL_META = {
    "name": "timeout",
    "func": "main",
    "desc": 'Run command with timeout limit',
}

if __name__ == '__main__':
    main()
