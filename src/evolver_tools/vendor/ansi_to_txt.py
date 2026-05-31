#!/usr/bin/env python3
"""ansi-to-txt — Convert ANSI-colored terminal output to plain text."""
TOOL_META = {"name": "ansi-to-txt", "desc": "Strip ANSI escape codes, convert to plain text", "func": "main"}

import sys
import re
import argparse


# Regex to match ANSI escape sequences
ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]|\x1b\][0-9;]*(?:\x07|\x1b\\)|\x1b[PX^_].*?(?:\x07|\x1b\\)')

# C1 control characters (rare but possible)
C1_CONTROLS = re.compile(r'[\x80-\x9a\x9c\x9b\x9d-\x9f]')


def strip_ansi(text):
    """Remove all ANSI escape sequences from text."""
    text = ANSI_ESCAPE.sub('', text)
    text = C1_CONTROLS.sub('', text)
    return text


def simplify_ansi(text):
    """Replace known ANSI formatting with simple markers."""
    # Bold → *text*
    text = re.sub(r'\x1b\[1m(.*?)\x1b\[0m', r'*\1*', text)
    text = re.sub(r'\x1b\[1m(.*?)\x1b\[(?:2[2-9]|3[0-7])?m', r'*\1*', text)
    # Underline → _text_
    text = re.sub(r'\x1b\[4m(.*?)\x1b\[0m', r'_\1_', text)
    # Remove all remaining sequences
    text = ANSI_ESCAPE.sub('', text)
    text = C1_CONTROLS.sub('', text)
    return text


def main():
    parser = argparse.ArgumentParser(
        description="Strip ANSI escape codes and convert to plain text.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  command-with-colors | ansi-to-txt
  ansi-to-txt --file output.log > clean.txt
  ls --color=always | ansi-to-txt
  make 2>&1 | ansi-to-txt --simplify
  cat ansi_output.txt | ansi-to-txt -o clean.txt
        """,
    )
    parser.add_argument("--file", "-f", help="File with ANSI codes to process")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    parser.add_argument("--simplify", "-s", action="store_true",
                        help="Replace bold/underline with *text*/_text_ markers instead of stripping")
    args = parser.parse_args()

    if args.file:
        try:
            with open(args.file, "rb") as f:
                raw = f.read()
        except FileNotFoundError:
            print(f"Error: file not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        raw = sys.stdin.buffer.read()

    # Decode with replacement for bad bytes
    text = raw.decode("utf-8", errors="replace")

    if args.simplify:
        result = simplify_ansi(text)
    else:
        result = strip_ansi(text)

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result)
        except Exception as e:
            print(f"Error writing: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        sys.stdout.write(result)


if __name__ == "__main__":
    main()
