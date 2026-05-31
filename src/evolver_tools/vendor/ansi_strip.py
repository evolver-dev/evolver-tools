#!/usr/bin/env python3
"""ansi-strip — Strip ANSI escape codes from text."""
import re
import sys

TOOL_META = {
    "name": "ansi-strip",
    "func": "main",
    "desc": "Strip ANSI escape codes. Usage: ansi-strip [file]",
}

ANSI_PATTERN = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def main():
    args = sys.argv[1:]
    if args and args[0] in ("-h", "--help"):
        print("Usage: ansi-strip [file]")
        print("       command_with_colors | ansi-strip")
        return
    if args:
        filepath = args[0]
        try:
            with open(filepath, "r") as f:
                text = f.read()
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        text = sys.stdin.read()
    result = ANSI_PATTERN.sub("", text)
    sys.stdout.write(result)

if __name__ == "__main__":
    main()
