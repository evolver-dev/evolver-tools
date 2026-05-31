"""diff_tool: Simple file comparator with color output.

Pure Python stdlib implementation using difflib.
Supports unified diff, context diff, ignore case/whitespace.
"""

import sys
import os
import difflib
import io

__version__ = "1.0.0"

# ANSI colors
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
BOLD = "\033[1m"
RESET = "\033[0m"
DIM = "\033[2m"


def read_file_or_stdin(path):
    """Read file content, or stdin if path is '-'."""
    if path == "-":
        return sys.stdin.read()
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except FileNotFoundError:
        print(f"diff: {path}: No such file", file=sys.stderr)
        sys.exit(1)
    except IsADirectoryError:
        print(f"diff: {path}: Is a directory", file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print(f"diff: {path}: Permission denied", file=sys.stderr)
        sys.exit(1)


def colorize_unified_diff(text):
    """Add ANSI colors to unified diff output."""
    lines = []
    for line in text.splitlines(True):
        if line.startswith("+++") or line.startswith("---"):
            lines.append(f"{BOLD}{CYAN}{line.rstrip()}{RESET}\n")
        elif line.startswith("@@"):
            lines.append(f"{YELLOW}{line.rstrip()}{RESET}\n")
        elif line.startswith("+"):
            lines.append(f"{GREEN}{line.rstrip()}{RESET}\n")
        elif line.startswith("-"):
            lines.append(f"{RED}{line.rstrip()}{RESET}\n")
        else:
            lines.append(line)
    return "".join(lines)


def colorize_context_diff(text):
    """Add ANSI colors to context diff output."""
    lines = []
    for line in text.splitlines(True):
        if line.startswith("***") or line.startswith("---"):
            lines.append(f"{BOLD}{CYAN}{line.rstrip()}{RESET}\n")
        elif line.startswith("***************"):
            lines.append(f"{BOLD}{YELLOW}{line.rstrip()}{RESET}\n")
        elif line.startswith("! ") or line.startswith("+ "):
            lines.append(f"{GREEN}{line.rstrip()}{RESET}\n")
        elif line.startswith("- "):
            lines.append(f"{RED}{line.rstrip()}{RESET}\n")
        else:
            lines.append(line)
    return "".join(lines)


def colorize_ndiff(text):
    """Add ANSI colors to ndiff output."""
    lines = []
    for line in text.splitlines(True):
        if line.startswith("? "):
            lines.append(f"{DIM}{line.rstrip()}{RESET}\n")
        elif line.startswith("+ "):
            lines.append(f"{GREEN}{line.rstrip()}{RESET}\n")
        elif line.startswith("- "):
            lines.append(f"{RED}{line.rstrip()}{RESET}\n")
        else:
            lines.append(line)
    return "".join(lines)


def print_help():
    print("Usage: diff [options] file1 file2")
    print()
    print("Compare two files and show differences.")
    print()
    print("Options:")
    print("  -u, --unified     Unified diff format (default)")
    print("  -c, --context     Context diff format")
    print("  -n, --ndiff       Columnar ndiff format")
    print("  -i, --ignore-case Case-insensitive comparison")
    print("  -w, --ignore-ws   Ignore whitespace differences")
    print("  -s, --stat        Show only summary statistics")
    print("  --no-color        Disable color output")
    print("  -h, --help        Show this help")
    print()
    print("Use '-' as filename to read from stdin.")
    print()
    print("Examples:")
    print("  diff old.py new.py")
    print("  diff -c file1.txt file2.txt")
    print("  diff -i config.yml config-prod.yml")
    print("  command1 | diff - file2.txt")


def main():
    args = sys.argv[1:]

    if not args or "-h" in args or "--help" in args:
        print_help()
        return

    fmt = "unified"
    ignore_case = False
    ignore_ws = False
    show_stat = False
    no_color = False

    # Parse flags
    file_args = []
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("-u", "--unified"):
            fmt = "unified"
        elif a in ("-c", "--context"):
            fmt = "context"
        elif a in ("-n", "--ndiff"):
            fmt = "ndiff"
        elif a in ("-i", "--ignore-case"):
            ignore_case = True
        elif a in ("-w", "--ignore-ws"):
            ignore_ws = True
        elif a in ("-s", "--stat"):
            show_stat = True
        elif a == "--no-color":
            no_color = True
        elif a.startswith("-"):
            print(f"diff: Unknown option: {a}", file=sys.stderr)
            print_help()
            sys.exit(1)
        else:
            file_args.append(a)
        i += 1

    if len(file_args) != 2:
        print("diff: Expected exactly 2 files (got {})".format(len(file_args)), file=sys.stderr)
        print_help()
        sys.exit(1)

    text_a = read_file_or_stdin(file_args[0])
    text_b = read_file_or_stdin(file_args[1])

    lines_a = text_a.splitlines(True)
    lines_b = text_b.splitlines(True)

    # Apply transformations
    if ignore_case:
        lines_a = [l.lower() for l in lines_a]
        lines_b = [l.lower() for l in lines_b]
    if ignore_ws:
        lines_a = [l.strip() + "\n" for l in lines_a]
        lines_b = [l.strip() + "\n" for l in lines_b]

    name_a = "stdin" if file_args[0] == "-" else file_args[0]
    name_b = "stdin" if file_args[1] == "-" else file_args[1]

    if fmt == "unified":
        diff = difflib.unified_diff(lines_a, lines_b, fromfile=name_a, tofile=name_b)
    elif fmt == "context":
        diff = difflib.context_diff(lines_a, lines_b, fromfile=name_a, tofile=name_b)
    else:
        diff = difflib.ndiff(lines_a, lines_b)

    diff_text = "".join(diff)

    if show_stat:
        added = diff_text.count("\n+") if fmt == "unified" else 0
        removed = diff_text.count("\n-") if fmt == "unified" else 0
        changed = diff_text.count("\n!") if fmt == "context" else 0
        print(f"--- {name_a}")
        print(f"+++ {name_b}")
        if fmt == "unified":
            print(f"{added} additions, {removed} deletions")
        else:
            print(f"{changed} changes")
        if not diff_text.strip():
            print("Files are identical")
        return

    if not diff_text.strip():
        print("Files are identical (0 differences)")
        return

    if no_color:
        sys.stdout.write(diff_text)
    elif fmt == "unified":
        sys.stdout.write(colorize_unified_diff(diff_text))
    elif fmt == "context":
        sys.stdout.write(colorize_context_diff(diff_text))
    else:
        sys.stdout.write(colorize_ndiff(diff_text))

    # Line count summary
    if fmt == "unified":
        adds = sum(1 for l in diff_text.split("\n") if l.startswith("+") and not l.startswith("+++"))
        rems = sum(1 for l in diff_text.split("\n") if l.startswith("-") and not l.startswith("---"))
        print(f"\n{DIM}{adds} addition(s), {rems} deletion(s){RESET}")

# === Auto-registration metadata ===
TOOL_META = {
    "name": "diff",
    "func": "main",
    "desc": 'File comparison and diff tool',
}
