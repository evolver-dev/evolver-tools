#!/usr/bin/env python3
"""markdown-toc — Generate a table of contents from markdown."""
import re
import sys

TOOL_META = {
    "name": "markdown-toc",
    "func": "main",
    "desc": "Generate table of contents from Markdown. Usage: markdown-toc [file.md]",
}

def main():
    args = sys.argv[1:]
    if args and args[0] in ("-h", "--help"):
        print("Usage: markdown-toc [file.md]")
        print("       cat file.md | markdown-toc")
        return
    if args:
        with open(args[0], "r") as f:
            content = f.read()
    else:
        content = sys.stdin.read()
    toc_lines = []
    for line in content.split("\n"):
        m = re.match(r"^(#{1,6})\s+(.+)$", line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            anchor = title.lower()
            anchor = re.sub(r"[^a-z0-9\s\-]", "", anchor)
            anchor = re.sub(r"\s+", "-", anchor.strip())
            indent = "  " * (level - 1)
            toc_lines.append(f"{indent}- [{title}](#{anchor})")
    if toc_lines:
        print("\n".join(toc_lines))
    else:
        print("(no headings found)")

if __name__ == "__main__":
    main()
