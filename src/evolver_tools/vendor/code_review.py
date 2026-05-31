#!/usr/bin/env python3
"""code-review: Static code review tool for Python files using AST analysis.

Analyzes Python files for common issues: long functions, too many parameters,
missing docstrings, TODO/FIXME comments, too many imports, duplicate code blocks,
and cyclomatic complexity.

Usage:
    code-review file1.py file2.py
    code-review --path src/
    code-review --path src/ --min-complexity 10 --json --verbose
"""

import ast
import os
import sys
import json
import glob
from collections import defaultdict

# ── Terminal Colors ──────────────────────────────────────────────────────────
COLORS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "white": "\033[97m",
    "dim": "\033[2m",
}
NO_COLORS = {k: "" for k in COLORS}


def _c(color_name, text, bold=False, use_color=True):
    """Return colorized text string."""
    c = COLORS if use_color else NO_COLORS
    b = c["bold"] if bold else ""
    return f"{b}{c.get(color_name, '')}{text}{c['reset']}"


# ── Issue Data ───────────────────────────────────────────────────────────────

class Issue:
    """Represents a single code review issue."""

    def __init__(self, issue_type, message, file_path, line=1, severity="info",
                 function_name=None):
        self.type = issue_type
        self.message = message
        self.file = file_path
        self.line = line
        self.severity = severity  # 'error', 'warning', 'info'
        self.function_name = function_name

    def to_dict(self):
        return {
            "type": self.type,
            "message": self.message,
            "file": self.file,
            "line": self.line,
            "severity": self.severity,
            "function": self.function_name,
        }

    def __repr__(self):
        return (
            f"[{self.severity.upper()}] {self.file}:{self.line} "
            f"({self.type}) {self.message}"
        )


# ── Analysis Functions ──────────────────────────────────────────────────────

def _get_source_lines(source):
    """Return list of lines from source string."""
    return source.splitlines()


def analyze_long_functions(tree, source_lines, file_path, max_lines=50):
    """Find functions with more than max_lines lines of body."""
    issues = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.body:
                continue
            first_line = node.body[0].lineno
            last_line = node.body[-1].end_lineno or node.body[-1].lineno
            body_length = last_line - first_line + 1
            if body_length > max_lines:
                issues.append(Issue(
                    issue_type="long-function",
                    message=(
                        f"Function '{node.name}' has {body_length} lines "
                        f"(max: {max_lines})"
                    ),
                    file_path=file_path,
                    line=node.lineno,
                    severity="warning",
                    function_name=node.name,
                ))
    return issues


def analyze_too_many_params(tree, file_path, max_params=5):
    """Find functions with more than max_params parameters."""
    issues = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Count positional + keyword-only + positional-keyword args
            args = node.args
            total = (
                len(args.args)
                + len(args.kwonlyargs)
                + len(args.posonlyargs)
            )
            # Don't count self/cls as a param
            if total > 0 and node.body:
                first_stmt = node.body[0]
                if isinstance(first_stmt, ast.Expr) and isinstance(first_stmt.value, ast.Constant):
                    # Has docstring — this is a real function
                    pass
                # Check if it's a method (first param named self or cls)
                method_extra = 0
                if args.args and args.args[0].arg in ("self", "cls"):
                    method_extra = 1

            effective = total
            if effective > max_params:
                issues.append(Issue(
                    issue_type="too-many-params",
                    message=(
                        f"Function '{node.name}' has {effective} parameters "
                        f"(max: {max_params})"
                    ),
                    file_path=file_path,
                    line=node.lineno,
                    severity="warning",
                    function_name=node.name,
                ))
    return issues


def analyze_missing_docstrings(tree, file_path):
    """Find functions, classes, and modules without docstrings."""
    issues = []

    # Module-level docstring
    if (not isinstance(tree.body[0], ast.Expr)
            or not isinstance(tree.body[0].value, ast.Constant)
            or not isinstance(tree.body[0].value.value, str)):
        issues.append(Issue(
            issue_type="missing-docstring",
            message="Module is missing a docstring",
            file_path=file_path,
            line=1,
            severity="info",
        ))

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if (not node.body
                    or not isinstance(node.body[0], ast.Expr)
                    or not isinstance(node.body[0].value, ast.Constant)
                    or not isinstance(node.body[0].value.value, str)):
                # Skip dunder methods
                if node.name.startswith("__") and node.name.endswith("__"):
                    continue
                issues.append(Issue(
                    issue_type="missing-docstring",
                    message=f"Function '{node.name}' is missing a docstring",
                    file_path=file_path,
                    line=node.lineno,
                    severity="info",
                    function_name=node.name,
                ))
        elif isinstance(node, ast.ClassDef):
            if (not node.body
                    or not isinstance(node.body[0], ast.Expr)
                    or not isinstance(node.body[0].value, ast.Constant)
                    or not isinstance(node.body[0].value.value, str)):
                issues.append(Issue(
                    issue_type="missing-docstring",
                    message=f"Class '{node.name}' is missing a docstring",
                    file_path=file_path,
                    line=node.lineno,
                    severity="info",
                ))
    return issues


def analyze_todo_comments(source, file_path):
    """Find TODO and FIXME comments in source."""
    issues = []
    for i, line in enumerate(source.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            lower = stripped.lower()
            if "todo" in lower:
                issues.append(Issue(
                    issue_type="todo-comment",
                    message=f"TODO comment found: {stripped.strip('# ')}",
                    file_path=file_path,
                    line=i,
                    severity="info",
                ))
            elif "fixme" in lower:
                issues.append(Issue(
                    issue_type="fixme-comment",
                    message=f"FIXME comment found: {stripped.strip('# ')}",
                    file_path=file_path,
                    line=i,
                    severity="warning",
                ))
    return issues


def analyze_imports(tree, file_path, max_imports=20):
    """Flag files with too many import statements."""
    count = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            count += 1
    issues = []
    if count > max_imports:
        issues.append(Issue(
            issue_type="too-many-imports",
            message=f"File has {count} import statements (max: {max_imports})",
            file_path=file_path,
            line=1,
            severity="info",
        ))
    return issues


def analyze_complexity(tree, file_path, min_complexity=10):
    """Calculate cyclomatic complexity and flag functions above threshold."""
    issues = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            complexity = 1  # Base complexity
            for child in ast.walk(node):
                if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                    complexity += 1
                elif isinstance(child, ast.ExceptHandler):
                    complexity += 1
                elif isinstance(child, (ast.With, ast.AsyncWith)):
                    complexity += 1
                elif isinstance(child, ast.BoolOp):
                    # Each 'and'/'or' adds to complexity
                    complexity += len(child.values) - 1
                elif isinstance(child, (ast.Assert,)):
                    complexity += 1
                elif isinstance(child, ast.Try):
                    complexity += len(child.handlers)

                # Ternary expressions: x if cond else y
                elif isinstance(child, ast.IfExp):
                    complexity += 1

            if complexity >= min_complexity:
                issues.append(Issue(
                    issue_type="high-complexity",
                    message=(
                        f"Function '{node.name}' has cyclomatic complexity "
                        f"of {complexity} (min: {min_complexity})"
                    ),
                    file_path=file_path,
                    line=node.lineno,
                    severity="warning",
                    function_name=node.name,
                ))
    return issues


def analyze_duplicate_code(tree, source_lines, file_path, min_block_lines=5):
    """Detect duplicate code blocks by comparing function body line hashes."""
    issues = []
    functions = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.body:
                continue
            first = node.body[0].lineno
            last = node.body[-1].end_lineno
            body_lines = source_lines[first - 1:last]
            # Normalize: strip indentation for comparison
            normalized = "\n".join(
                line.strip() for line in body_lines
                if line.strip() and not line.strip().startswith("#")
            )
            functions.append((node.name, first, normalized))

    # Compare each pair of functions
    seen = set()
    for i, (name_a, line_a, body_a) in enumerate(functions):
        for j, (name_b, line_b, body_b) in enumerate(functions):
            if i >= j:
                continue
            if body_a and body_a == body_b and len(body_a.splitlines()) >= min_block_lines:
                pair_key = tuple(sorted([name_a, name_b]))
                if pair_key not in seen:
                    seen.add(pair_key)
                    nlines = body_a.count("\n") + 1
                    issues.append(Issue(
                        issue_type="duplicate-code",
                        message=(
                            f"Functions '{name_a}' (line {line_a}) and "
                            f"'{name_b}' (line {line_b}) have identical "
                            f"body ({nlines} lines)"
                        ),
                        file_path=file_path,
                        line=line_a,
                        severity="info",
                        function_name=name_a,
                    ))
    return issues


# ── File Processing ──────────────────────────────────────────────────────────

def analyze_file(file_path, max_lines=50, max_params=5, max_imports=20,
                 min_complexity=10, verbose=False):
    """Analyze a single Python file and return list of Issues."""
    issues = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
    except (OSError, IOError) as e:
        issues.append(Issue(
            issue_type="io-error",
            message=f"Cannot read file: {e}",
            file_path=file_path,
            line=1,
            severity="error",
        ))
        return issues

    try:
        tree = ast.parse(source, filename=file_path)
    except SyntaxError as e:
        issues.append(Issue(
            issue_type="syntax-error",
            message=f"Syntax error: {e.msg} (line {e.lineno})",
            file_path=file_path,
            line=e.lineno or 1,
            severity="error",
        ))
        return issues

    source_lines = source.splitlines()

    checks = [
        ("long-functions", lambda: analyze_long_functions(
            tree, source_lines, file_path, max_lines)),
        ("too-many-params", lambda: analyze_too_many_params(
            tree, file_path, max_params)),
        ("missing-docstrings", lambda: analyze_missing_docstrings(
            tree, file_path)),
        ("todo-fixme", lambda: analyze_todo_comments(source, file_path)),
        ("imports", lambda: analyze_imports(tree, file_path, max_imports)),
        ("complexity", lambda: analyze_complexity(
            tree, file_path, min_complexity)),
        ("duplicate-code", lambda: analyze_duplicate_code(
            tree, source_lines, file_path)),
    ]

    if verbose:
        for name, check in checks:
            result = check()
            issues.extend(result)
            if result:
                print(f"  Check '{name}': {len(result)} issue(s)", file=sys.stderr)
    else:
        for _, check in checks:
            issues.extend(check())

    return issues


def collect_py_files(paths):
    """Collect all .py files from given paths (files or directories)."""
    files = []
    for p in paths:
        if os.path.isfile(p):
            if p.endswith(".py"):
                files.append(p)
        elif os.path.isdir(p):
            for root, dirs, fnames in os.walk(p):
                # Skip common non-source dirs
                dirs[:] = [d for d in dirs
                           if not d.startswith(".")
                           and d not in ("__pycache__", "node_modules",
                                         "venv", ".venv", "env", ".env",
                                         "dist", "build", "eggs", ".eggs")]
                for fname in fnames:
                    if fname.endswith(".py"):
                        files.append(os.path.join(root, fname))
        else:
            print(
                _c("red", f"Error: path not found: {p}"),
                file=sys.stderr,
            )
    return sorted(set(files))


# ── Output Formatting ────────────────────────────────────────────────────────

def print_issue(issue, verbose=False, use_color=True):
    """Print a single issue with colorized output."""
    severity_colors = {
        "error": "red",
        "warning": "yellow",
        "info": "cyan",
    }
    severity_labels = {
        "error": "ERROR",
        "warning": "WARN",
        "info": "INFO",
    }

    color = severity_colors.get(issue.severity, "white")
    label = severity_labels.get(issue.severity, "INFO")

    parts = [
        _c(color, f"[{label}]", use_color=use_color),
        _c("white", f" {issue.file}:{issue.line}", bold=True, use_color=use_color),
        _c("dim", f"  {issue.type}", use_color=use_color),
        _c("reset", f"  {issue.message}", use_color=use_color),
    ]

    if verbose and issue.function_name:
        parts.append(_c("magenta", f"  (in {issue.function_name})",
                       use_color=use_color))

    print("".join(parts))


def print_summary(files_analyzed, total_issues, by_severity, use_color=True):
    """Print a summary of the review."""
    sep = _c("dim", "─" * 60, use_color=use_color)
    print()
    print(sep)
    print(_c("bold", "  Code Review Summary", use_color=use_color))
    print(sep)
    print(f"  Files analyzed: {_c('green', str(files_analyzed), use_color=use_color)}")
    print(f"  Total issues:   {_c('yellow', str(total_issues), use_color=use_color)}")
    if by_severity.get("error"):
        print(f"  Errors:          {_c('red', str(by_severity['error']), use_color=use_color)}")
    if by_severity.get("warning"):
        print(f"  Warnings:        {_c('yellow', str(by_severity['warning']), use_color=use_color)}")
    if by_severity.get("info"):
        print(f"  Info:            {_c('cyan', str(by_severity['info']), use_color=use_color)}")
    print(sep)


def print_file_header(file_path, use_color=True):
    """Print a header for a file section."""
    print()
    print(_c("blue", f"  ── {file_path}", bold=True, use_color=use_color))


# ── Main CLI ────────────────────────────────────────────────────────────────

TOOL_META = {
    "name": "code-review",
    "func": "main",
    "desc": "Static code review for Python files (AST analysis)",
    "usage": (
        "code-review [files...] [--path DIR] [--min-complexity N] "
        "[--json] [--verbose]"
    ),
}


def main(argv=None):
    """Main entry point. Parses args and runs the review."""
    if argv is None:
        argv = sys.argv[1:]

    # Parse args manually (pure stdlib)
    paths = []
    target_dir = None
    min_complexity = 10
    json_output = False
    verbose = False

    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--path":
            i += 1
            if i >= len(argv):
                print("Error: --path requires a directory argument",
                      file=sys.stderr)
                return 1
            target_dir = argv[i]
        elif arg == "--min-complexity":
            i += 1
            if i >= len(argv):
                print("Error: --min-complexity requires a number",
                      file=sys.stderr)
                return 1
            try:
                min_complexity = int(argv[i])
            except ValueError:
                print(f"Error: --min-complexity must be an integer, got '{argv[i]}'",
                      file=sys.stderr)
                return 1
        elif arg == "--json":
            json_output = True
        elif arg == "--verbose":
            verbose = True
        elif arg.startswith("-"):
            print(
                f"Error: Unknown argument '{arg}'. "
                f"Usage: {TOOL_META['usage']}",
                file=sys.stderr,
            )
            return 1
        else:
            paths.append(arg)
        i += 1

    # Determine files to analyze
    if target_dir:
        if paths:
            print(
                "Warning: --path and file arguments both provided. "
                "Using --path only.",
                file=sys.stderr,
            )
        paths = [target_dir]

    if not paths:
        # Default to current directory
        paths = ["."]

    py_files = collect_py_files(paths)

    if not py_files:
        print(
            _c("yellow", "No Python files found to analyze."),
            file=sys.stderr,
        )
        return 0

    # Analyze all files
    all_issues = {}
    for f in py_files:
        if verbose:
            print(
                _c("dim", f"Analyzing {f}...", use_color=not json_output),
                file=sys.stderr,
            )
        issues = analyze_file(
            f,
            min_complexity=min_complexity,
            verbose=verbose,
        )
        if issues:
            all_issues[f] = issues

    # Flatten for summary
    flat_issues = [iss for iss_list in all_issues.values()
                   for iss in iss_list]
    total_issues = len(flat_issues)
    files_analyzed = len(py_files)

    # Count by severity
    by_severity = defaultdict(int)
    for iss in flat_issues:
        by_severity[iss.severity] += 1

    # Output
    if json_output:
        output = {
            "tool": "code-review",
            "files_analyzed": files_analyzed,
            "total_issues": total_issues,
            "issues_by_severity": dict(by_severity),
            "issues": [iss.to_dict() for iss in flat_issues],
        }
        print(json.dumps(output, indent=2))
    else:
        use_color = sys.stdout.isatty() and os.name != "nt"
        for fpath, issues in all_issues.items():
            print_file_header(fpath, use_color=use_color)
            for iss in issues:
                print_issue(iss, verbose=verbose, use_color=use_color)

        print_summary(
            files_analyzed, total_issues, by_severity,
            use_color=use_color,
        )

    return 1 if total_issues > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
