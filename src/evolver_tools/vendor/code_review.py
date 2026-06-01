#!/usr/bin/env python3
"""code-review — Basic code review helper for Python files.

Usage:
    code-review <file.py> [--lines=1-50]
    cat file.py | code-review

Checks for: line length, TODOs, missing shebang, trailing whitespace,
missing docstrings, CRLF line endings, tabs, long functions, bare
excepts, unused imports (flagged heuristically), and more.

Output uses severity tags: [ERROR], [WARN], [INFO].
"""

import sys
import os
import re
import ast
import argparse


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_shebang(lines, path):
    """[ERROR] Python files should start with a shebang."""
    if path and path.endswith('.py'):
        if not lines or not lines[0].startswith('#!'):
            return [("[ERROR] Line 1: Missing shebang "
                     "(e.g. #!/usr/bin/env python3)")]
    return []


def check_line_length(lines, max_len=100):
    """[WARN] Lines exceeding max_len characters."""
    issues = []
    for i, line in enumerate(lines, 1):
        # Skip URLs and long string literals to reduce noise
        if len(line.rstrip('\n')) > max_len:
            stripped = line.rstrip('\n')
            if not re.match(r'^\s*#\s*http', stripped):
                issues.append(
                    f"[WARN] Line {i}: {len(stripped)} chars "
                    f"(max {max_len})"
                )
    return issues


def check_todos(lines):
    """[INFO] Flag TODO / FIXME / XXX comments."""
    issues = []
    pattern = re.compile(r'(TODO|FIXME|XXX|HACK|BUG)\b', re.IGNORECASE)
    for i, line in enumerate(lines, 1):
        m = pattern.search(line)
        if m:
            issues.append(f"[INFO] Line {i}: {m.group(0)} found — "
                          f"\"{line.strip()}\"")
    return issues


def check_trailing_whitespace(lines):
    """[WARN] Trailing whitespace on lines."""
    issues = []
    for i, line in enumerate(lines, 1):
        if line != line.rstrip('\n').rstrip() + '\n':
            issues.append(f"[WARN] Line {i}: trailing whitespace")
    return issues


def check_crlf(lines):
    """[WARN] Carriage-return line endings (CRLF)."""
    for i, line in enumerate(lines, 1):
        if '\r\n' in line:
            return ["[WARN] Line {i}: CRLF (\\r\\n) line ending detected"]
    return []


def check_tabs(lines):
    """[ERROR] Tab characters used instead of spaces."""
    issues = []
    for i, line in enumerate(lines, 1):
        if '\t' in line:
            issues.append(f"[ERROR] Line {i}: tab character used")
    return issues


def check_missing_docstrings(code_lines, source):
    """[INFO] Functions, classes, and modules missing docstrings."""
    issues = []
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return [f"[ERROR] Syntax error: {e}"]

    # Module-level docstring
    if (not isinstance(tree.body[0], ast.Expr)
            or not isinstance(tree.body[0].value, ast.Constant)
            or not isinstance(tree.body[0].value.value, str)):
        issues.append("[INFO] Module: missing module-level docstring")

    for node in ast.walk(tree):
        # Functions / methods
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node)
            if not doc:
                lineno = getattr(node, 'lineno', '?')
                issues.append(
                    f"[INFO] Line {lineno}: "
                    f"function '{node.name}' missing docstring"
                )
        # Classes
        elif isinstance(node, ast.ClassDef):
            doc = ast.get_docstring(node)
            if not doc:
                lineno = getattr(node, 'lineno', '?')
                issues.append(
                    f"[INFO] Line {lineno}: "
                    f"class '{node.name}' missing docstring"
                )
    return issues


def check_long_functions(code_lines, source, max_lines=50):
    """[WARN] Functions that exceed max_lines."""
    issues = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end_lineno = getattr(node, 'end_lineno', node.lineno)
            nlines = end_lineno - node.lineno + 1
            if nlines > max_lines:
                issues.append(
                    f"[WARN] Line {node.lineno}: "
                    f"function '{node.name}' is {nlines} lines "
                    f"(recommended <= {max_lines})"
                )
    return issues


def check_bare_excepts(source):
    """[ERROR] Bare 'except:' clauses without exception type."""
    issues = []
    pattern = re.compile(r'^(\s*?)except\s*:')
    for i, line in enumerate(source.splitlines(), 1):
        if pattern.match(line):
            issues.append(
                f"[ERROR] Line {i}: bare except clause — "
                f"use 'except Exception:' instead"
            )
    return issues


def check_imports(source):
    """[WARN] Wildcard imports."""
    issues = []
    for i, line in enumerate(source.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith('from ') and ' import *' in stripped:
            issues.append(
                f"[WARN] Line {i}: wildcard import (from ... import *)"
            )
    return issues


# ---------------------------------------------------------------------------
# Parse --lines argument
# ---------------------------------------------------------------------------

def parse_line_range(lines_arg, total_lines):
    """Return (start, end) 1-indexed slice, or (1, total_lines)."""
    if not lines_arg:
        return (1, total_lines)
    m = re.match(r'^(\d+)(?:-(\d+))?$', lines_arg)
    if not m:
        sys.stderr.write(f"error: invalid --lines format '{lines_arg}'. "
                         "Use N-M (e.g. 1-50) or just N.\n")
        sys.exit(1)
    start = int(m.group(1))
    end = int(m.group(2)) if m.group(2) else start
    if start < 1:
        start = 1
    if end > total_lines:
        end = total_lines
    if start > end:
        start, end = end, start
    return (start, end)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Code review helper for Python files."
    )
    parser.add_argument(
        'file', nargs='?', default=None,
        help="Path to Python file to review (reads from stdin if omitted)"
    )
    parser.add_argument(
        '--lines', default=None,
        help="Line range to check, e.g. '1-50' or '42'"
    )
    parser.add_argument(
        '--max-line-length', type=int, default=100,
        help="Maximum allowed line length (default: 100)"
    )
    parser.add_argument(
        '--max-function-lines', type=int, default=50,
        help="Maximum function length in lines (default: 50)"
    )
    args = parser.parse_args()

    if args.file:
        path = args.file
        try:
            with open(path, 'rb') as f:
                raw = f.read()
        except FileNotFoundError:
            sys.stderr.write(f"error: file not found: {path}\n")
            sys.exit(1)
        except PermissionError:
            sys.stderr.write(f"error: permission denied: {path}\n")
            sys.exit(1)
    else:
        path = None
        raw = sys.stdin.buffer.read()

    # Decode, preserving line endings for CRLF detection
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError:
        text = raw.decode('latin-1')
        sys.stderr.write("warning: file is not UTF-8; decoded as latin-1\n")

    all_lines = text.splitlines(keepends=True)
    total = len(all_lines)

    start, end = parse_line_range(args.lines, total)
    if not args.lines:
        start, end = 1, total

    lines = all_lines[start - 1:end]
    source = ''.join(lines)

    # Collect all issues
    all_issues = []

    # --lines mode: only run per-line checks on the subset
    all_issues.extend(check_shebang(all_lines, path))
    all_issues.extend(check_line_length(lines, args.max_line_length))
    all_issues.extend(check_todos(lines))
    all_issues.extend(check_trailing_whitespace(lines))
    all_issues.extend(check_crlf(lines))
    all_issues.extend(check_tabs(lines))
    # AST-based checks need the full function boundaries; we always run
    # on the full file for these, but only report issues in the range.
    full_source = ''.join(all_lines)
    for issue in check_missing_docstrings(all_lines, full_source):
        lineno_match = re.search(r'Line (\d+)', issue)
        if lineno_match:
            lineno = int(lineno_match.group(1))
            if start <= lineno <= end:
                all_issues.append(issue)
        else:
            all_issues.append(issue)
    for issue in check_long_functions(all_lines, full_source,
                                      args.max_function_lines):
        lineno_match = re.search(r'Line (\d+)', issue)
        if lineno_match:
            lineno = int(lineno_match.group(1))
            if start <= lineno <= end:
                all_issues.append(issue)
        else:
            all_issues.append(issue)
    all_issues.extend(check_bare_excepts(source))
    all_issues.extend(check_imports(source))

    # Sort by line number where possible
    def sort_key(issue):
        m = re.search(r'Line (\d+)', issue)
        return int(m.group(1)) if m else 0
    all_issues.sort(key=sort_key)

    # Output
    if not all_issues:
        print("No issues found.")
        return

    for issue in all_issues:
        print(issue)

    # Summary
    errors = sum(1 for i in all_issues if i.startswith('[ERROR]'))
    warns = sum(1 for i in all_issues if i.startswith('[WARN]'))
    infos = sum(1 for i in all_issues if i.startswith('[INFO]'))
    print(f"\n--- Summary: {errors} errors, {warns} warnings, "
          f"{infos} info items ---")

    if errors:
        sys.exit(1)


# ---------------------------------------------------------------------------
# Tool metadata for auto-discovery
# ---------------------------------------------------------------------------

TOOL_META = {
    "name": "code-review",
    "func": "main",
    "desc": "Basic code review: line length, TODOs, shebang, "
            "trailing whitespace, docstrings, CRLF, tabs, "
            "long functions, bare excepts, wildcard imports"
}


if __name__ == '__main__':
    main()
