#!/usr/bin/env python3
"""markdown-preview — Preview Markdown in terminal with syntax highlighting."""
import re
import sys

TOOL_META = {
    "name": "markdown-preview",
    "func": "main",
    "desc": "Preview Markdown in terminal. Usage: markdown-preview <file.md>",
}

def render_markdown(text):
    lines = text.split("\n")
    output = []
    in_code_block = False
    for line in lines:
        # Code blocks
        if line.startswith("```"):
            in_code_block = not in_code_block
            if in_code_block:
                output.append("\033[1;30m┌─── code ──────────────────────────────────────┐\033[0m")
            else:
                output.append("\033[1;30m└──────────────────────────────────────────────┘\033[0m")
            continue
        if in_code_block:
            output.append(f"\033[2;37m  {line}\033[0m")
            continue
        # Headings
        m = re.match(r"^(#{1,6})\s+(.+)$", line)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            if level == 1:
                output.append(f"\n\033[1;36m{'═' * 50}\033[0m")
                output.append(f"\033[1;36m  {text}\033[0m")
                output.append(f"\033[1;36m{'═' * 50}\033[0m\n")
            elif level == 2:
                output.append(f"\n\033[1;33m  {text}\033[0m")
                output.append(f"\033[1;33m  {'─' * min(len(text), 50)}\033[0m\n")
            elif level == 3:
                output.append(f"\n\033[1;34m  ### {text}\033[0m\n")
            else:
                output.append(f"\n\033[1;37m  {'#' * level} {text}\033[0m\n")
            continue
        # Horizontal rules
        if re.match(r"^[-*_]{3,}$", line.strip()):
            output.append(f"\033[1;30m  {'─' * 50}\033[0m")
            continue
        # Blockquotes
        if line.startswith(">"):
            content = line[1:].strip()
            output.append(f"\033[2;33m  │ {content}\033[0m")
            continue
        # Unordered lists
        if re.match(r"^[\s]*[-*+]\s+", line):
            indent = len(line) - len(line.lstrip())
            content = re.sub(r"^[\s]*[-*+]\s+", "", line)
            prefix = "  " * (indent // 2) + "•"
            output.append(f"  {prefix} {content}")
            continue
        # Ordered lists
        m = re.match(r"^(\s*)\d+[.)]\s+(.+)$", line)
        if m:
            output.append(f"  {m.group(1)}{m.group(2)}")
            continue
        # Inline code
        line = re.sub(r"`([^`]+)`", r"\033[1;32m\1\033[0m", line)
        # Bold
        line = re.sub(r"\*\*(.+?)\*\*", r"\033[1;37m\1\033[0m", line)
        # Italic
        line = re.sub(r"\*(.+?)\*", r"\033[3;37m\1\033[0m", line)
        # Links [text](url)
        line = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\033[1;34m\1\033[0m (\033[4;34m\2\033[0m)", line)
        # Empty line
        if line.strip() == "":
            output.append("")
        else:
            output.append(f"  {line}")
    return "\n".join(output)

def main():
    args = sys.argv[1:]
    if args and args[0] in ("-h", "--help"):
        print("Usage: markdown-preview <file.md>")
        print("       cat file.md | markdown-preview")
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
    print(render_markdown(text))

if __name__ == "__main__":
    main()
