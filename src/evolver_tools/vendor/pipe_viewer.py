#!/usr/bin/env python3
"""pipe-viewer — Pipe viewer with progress bar for piped data."""
import os
import sys
import time

TOOL_META = {
    "name": "pipe-viewer",
    "func": "main",
    "desc": "Pipe viewer with progress bar. Usage: cmd | pipe-viewer [label]",
}

def format_bytes(size):
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

def main():
    args = sys.argv[1:]
    label = " ".join(args) if args else "Processing"
    if not sys.stdin.isatty():
        chunk_size = 4096
        total = 0
        start = time.time()
        try:
            # Try to get total size from stdin if it's a file
            total_expected = None
            try:
                total_expected = os.fstat(sys.stdin.buffer.fileno()).st_size
            except Exception:
                pass
            while True:
                chunk = sys.stdin.buffer.read(chunk_size)
                if not chunk:
                    break
                sys.stdout.buffer.write(chunk)
                total += len(chunk)
                elapsed = time.time() - start
                if elapsed > 0:
                    speed = total / elapsed
                    if total_expected:
                        pct = min(100, total * 100 / max(total_expected, 1))
                        bar_len = 30
                        filled = int(bar_len * pct / 100)
                        bar = "█" * filled + "░" * (bar_len - filled)
                        eta = (total_expected - total) / max(speed, 1)
                        print(f"\r{label}: |{bar}| {pct:.0f}% {format_bytes(total)}/{format_bytes(total_expected)} {format_bytes(speed)}/s ETA:{eta:.0f}s", end="", file=sys.stderr)
                    else:
                        print(f"\r{label}: {format_bytes(total)} @ {format_bytes(speed)}/s [{elapsed:.1f}s]", end="", file=sys.stderr)
                sys.stdout.buffer.flush()
            sys.stdout.buffer.flush()
            elapsed = time.time() - start
            speed = total / max(elapsed, 0.001)
            print(f"\r✓ {label}: {format_bytes(total)} in {elapsed:.1f}s ({format_bytes(speed)}/s)    ", file=sys.stderr)
        except KeyboardInterrupt:
            elapsed = time.time() - start
            speed = total / max(elapsed, 0.001)
            print(f"\r⚠ {label}: {format_bytes(total)} in {elapsed:.1f}s (interrupted)", file=sys.stderr)
            sys.exit(1)
    else:
        print("pipe-viewer: pipe data through stdin (e.g., cat file | pipe-viewer 'Copying')", file=sys.stderr)
        print("Usage: command | pipe-viewer [label]", file=sys.stderr)
        # Just pass through
        try:
            while True:
                chunk = sys.stdin.buffer.read(4096)
                if not chunk:
                    break
                sys.stdout.buffer.write(chunk)
            sys.stdout.buffer.flush()
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    main()
