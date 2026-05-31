#!/usr/bin/env python3
"""slugify — Convert text to URL-friendly ASCII slugs.

Usage: slugify <text>
       echo "Hello World!" | slugify

Reads from a positional argument or stdin. Outputs a lowercase slug
with hyphens replacing spaces and non-ASCII characters stripped.
"""

import sys
import re
import unicodedata

TOOL_META = {
    "name": "slugify",
    "func": "main",
    "desc": "Convert text to URL-friendly ASCII slugs",
}


def slugify(text):
    """Convert text to a URL-friendly ASCII slug."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s]+", "-", text)
    text = re.sub(r"-+", "-", text)
    text = text.strip("-")
    return text


def main():
    args = sys.argv[1:]

    if "-h" in args or "--help" in args:
        print(__doc__)
        return

    if args:
        text = " ".join(args)
    else:
        text = sys.stdin.read().strip()

    print(slugify(text))


if __name__ == "__main__":
    main()
