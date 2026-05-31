#!/usr/bin/env python3
"""screenshot-cli — Take screenshots from the terminal."""
import subprocess
import sys
import tempfile
import os
from datetime import datetime

TOOL_META = {
    "name": "screenshot-cli",
    "func": "main",
    "desc": "Take screenshots from terminal. Usage: screenshot-cli [output.png] [--delay N]",
}

def main():
    delay = 0
    output = None
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--delay" and i + 1 < len(args):
            delay = int(args[i + 1])
            i += 2
        elif args[i].startswith("--delay="):
            delay = int(args[i].split("=", 1)[1])
            i += 1
        elif not args[i].startswith("-"):
            output = args[i]
            i += 1
        else:
            i += 1
    if not output:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = f"screenshot_{ts}.png"
    try:
        import pyscreenshot as ImageGrab
    except ImportError:
        # Fallback: check for importlib
        try:
            from PIL import ImageGrab
        except ImportError:
            print("Error: Install pyscreenshot or Pillow: pip install pyscreenshot", file=sys.stderr)
            sys.exit(1)
    import time
    if delay > 0:
        print(f"Taking screenshot in {delay}s...")
        time.sleep(delay)
    try:
        img = ImageGrab.grab()
        img.save(output)
        print(f"Screenshot saved: {output}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
