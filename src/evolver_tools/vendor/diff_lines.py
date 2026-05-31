#!/usr/bin/env python3
"""diff-lines — Line-by-line diff between two files.

Simple, zero-dependency diff tool.
Shows added (+), removed (-), and unchanged ( ) lines.
Similar to `diff -u` output but cleaner.

Usage:
    diff-lines file1.txt file2.txt
    diff-lines --side-by-side a.txt b.txt
"""

import sys
import os

TOOL_META = {
    "name": "diff-lines",
    "func": "main",
    "desc": "Line-by-line diff between two files (zero-dependency)",
}


def read_lines(path):
    """Read file lines, stripping trailing newline."""
    label = path
    if path == "-":
        return [l.rstrip("\n\r") for l in sys.stdin], "<stdin>"
    with open(path, encoding="utf-8", errors="replace") as f:
        return [l.rstrip("\n\r") for l in f], label


def lcs_diff(a, b):
    """Compute a simple diff using longest-common-subsequence approach."""
    m, n = len(a), len(b)

    # Build LCS table
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    # Backtrack to get diff
    i, j = m, n
    result = []
    while i > 0 or j > 0:
        if i > 0 and j > 0 and a[i - 1] == b[j - 1]:
            result.append((" ", a[i - 1]))
            i -= 1
            j -= 1
        elif j > 0 and (i == 0 or dp[i][j - 1] >= dp[i - 1][j]):
            result.append(("+", b[j - 1]))
            j -= 1
        else:
            result.append(("-", a[i - 1]))
            i -= 1

    result.reverse()
    return result


def print_diff(diff, label_a, label_b):
    """Print unified diff format."""
    added = sum(1 for op, _ in diff if op == "+")
    removed = sum(1 for op, _ in diff if op == "-")
    unchanged = sum(1 for op, _ in diff if op == " ")

    print(f"--- {label_a}")
    print(f"+++ {label_b}")
    print()

    for op, line in diff:
        if op == " ":
            print(f"  {line}")
        elif op == "+":
            print(f"\033[32m+ {line}\033[0m")
        elif op == "-":
            print(f"\033[31m- {line}\033[0m")

    print()
    print(f"{unchanged} unchanged, {added} added, {removed} removed")


def print_side_by_side(diff, label_a, label_b, width=40):
    """Print side-by-side diff."""
    added = 0
    removed = 0
    unchanged = 0

    # Collect lines for each side
    left_lines = []
    right_lines = []

    for op, line in diff:
        if op == " ":
            left_lines.append((op, line))
            right_lines.append((op, line))
            unchanged += 1
        elif op == "-":
            left_lines.append(("-", line))
            right_lines.append(("+", ""))
            removed += 1
        elif op == "+":
            left_lines.append(("-", ""))
            right_lines.append(("+", line))
            added += 1

    bar = " │ "
    for (lop, lline), (rop, rline) in zip(left_lines, right_lines):
        lcol = "\033[31m" if lop == "-" else ""
        rcol = "\033[32m" if rop == "+" else ""
        reset = "\033[0m" if lop in ("-",) or rop in ("+",) else ""
        ldisplay = lline[:width].ljust(width)
        rdisplay = rline[:width].ljust(width)
        print(f"{lcol}{ldisplay}{reset}{bar}{rcol}{rdisplay}{reset}")

    print(f"\n{unchanged} unchanged, {added} added, {removed} removed")


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print("Usage: diff-lines [--side-by-side] <file1> <file2>")
        print("       diff-lines <file1> <file2>   # Unified diff with color")
        print("       diff-lines -s a.txt b.txt    # Side-by-side view")
        print("       Use '-' for stdin")
        return

    side_by_side = False
    files = [a for a in args if not a.startswith("--") and not a.startswith("-")]

    # Check for flags
    for arg in args:
        if arg in ("--side-by-side", "-s"):
            side_by_side = True

    if len(files) < 2:
        print("Error: need two files to diff", file=sys.stderr)
        sys.exit(1)

    file_a, file_b = files[0], files[1]

    try:
        lines_a, label_a = read_lines(file_a)
        lines_b, label_b = read_lines(file_b)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    diff = lcs_diff(lines_a, lines_b)

    if side_by_side:
        print_side_by_side(diff, label_a, label_b)
    else:
        print_diff(diff, label_a, label_b)

    if any(op in ("+", "-") for op, _ in diff):
        sys.exit(0)  # files differ but that's not an error
    sys.exit(0)


if __name__ == "__main__":
    main()
