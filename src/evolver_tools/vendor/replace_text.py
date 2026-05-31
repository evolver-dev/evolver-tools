#!/usr/bin/env python3
"""replace-text — Find and replace text in files."""
import os
import re
import sys

TOOL_META = {
    "name": "replace-text",
    "func": "main",
    "desc": "Find and replace text in files. Usage: replace-text <old> <new> [files...] [--dry-run]",
}

def main():
    args = sys.argv[1:]
    if len(args) < 2 or args[0] in ("-h", "--help"):
        print("Usage: replace-text <old> <new> [files...] [--dry-run] [--regex]")
        print("       cat file | replace-text <old> <new>")
        sys.exit(1)
    old_text = args[0]
    new_text = args[1]
    files = []
    dry_run = False
    use_regex = False
    i = 2
    while i < len(args):
        if args[i] == "--dry-run":
            dry_run = True
        elif args[i] == "--regex":
            use_regex = True
        elif args[i].startswith("-"):
            pass  # skip other flags
        else:
            files.append(args[i])
        i += 1
    if not files:
        # Stdin mode
        content = sys.stdin.read()
        if use_regex:
            new_content = re.sub(old_text, new_text, content)
        else:
            new_content = content.replace(old_text, new_text)
        sys.stdout.write(new_content)
        return
    total_replaced = 0
    for fp in files:
        if not os.path.exists(fp):
            print(f"File not found: {fp}", file=sys.stderr)
            continue
        try:
            with open(fp, "r") as f:
                content = f.read()
            if use_regex:
                new_content, count = re.subn(old_text, new_text, content)
            else:
                count = content.count(old_text)
                new_content = content.replace(old_text, new_text)
            if count > 0:
                if dry_run:
                    print(f"  {fp}: would replace {count} occurrence(s)")
                else:
                    with open(fp, "w") as f:
                        f.write(new_content)
                    print(f"  {fp}: replaced {count} occurrence(s)")
                total_replaced += count
        except Exception as e:
            print(f"  {fp}: error — {e}", file=sys.stderr)
    if dry_run:
        print(f"Dry run: {total_replaced} total replacements would be made")
    else:
        print(f"Done: {total_replaced} total replacements made")

if __name__ == "__main__":
    main()
