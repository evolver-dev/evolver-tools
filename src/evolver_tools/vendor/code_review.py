#!/usr/bin/env python3
"""code-review — Automated code review suggestions for Python files."""
import os, sys, re, ast, json
from pathlib import Path
from collections import defaultdict

TOOL_META = {
    "name": "code-review",
    "desc": "Automated code review for Python files (style, complexity, security)",
    "func": "main",
}

class CodeReviewer(ast.NodeVisitor):
    REVIEWS = []

    def __init__(self, source, filename=""):
        self.source = source
        self.lines = source.split("\n")
        self.filename = filename
        self.issues = []
        self.func_count = 0
        self.class_count = 0

    def add(self, severity, msg, line=0, col=0, category="style"):
        self.issues.append({
            "severity": severity,
            "msg": msg,
            "line": line,
            "col": col,
            "file": self.filename,
            "category": category,
        })

    def visit_FunctionDef(self, node):
        self.func_count += 1
        # Check function length
        if hasattr(node, "end_lineno") and node.end_lineno:
            length = node.end_lineno - node.lineno
            if length > 50:
                self.add("warning", f"Function too long ({length} lines)", node.lineno, category="complexity")
            elif length > 30:
                self.add("info", f"Long function ({length} lines, consider refactoring)", node.lineno, category="complexity")
        # Check missing docstring
        if not ast.get_docstring(node):
            self.add("info", f"Missing docstring", node.lineno, category="style")
        # Check number of arguments
        args = node.args.args + node.args.kwonlyargs
        if len(args) > 7:
            self.add("warning", f"Too many arguments ({len(args)})", node.lineno, category="complexity")
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node):
        self.class_count += 1
        if not ast.get_docstring(node):
            self.add("info", f"Missing class docstring", node.lineno, category="style")
        self.generic_visit(node)

    def visit_Call(self, node):
        # Check for dangerous functions
        if isinstance(node.func, ast.Name):
            if node.func.id in ("eval", "exec", "__import__"):
                self.add("error", f"Dangerous function: {node.func.id}()", node.lineno, category="security")
            if node.func.id == "input" and sys.version_info >= (3,):
                self.add("warning", "input() in Python 3 returns strings (safe), but check usage", node.lineno, category="security")
        self.generic_visit(node)

    def visit_Try(self, node):
        # Check bare except
        for handler in node.handlers:
            if handler.type is None:
                self.add("warning", "Bare 'except:' clause (catches all exceptions)", node.lineno, category="security")
        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            if alias.asname and "_" not in alias.asname and alias.asname[0].islower() and len(alias.asname) < 3:
                self.add("info", f"Short alias '{alias.asname}' for {alias.name}", node.lineno, category="style")
        self.generic_visit(node)

    def check_style(self):
        """Check line-level style issues."""
        for i, line in enumerate(self.lines, 1):
            # Trailing whitespace
            if line.rstrip() != line and line.strip():
                self.add("info", "Trailing whitespace", i, category="style")
            # Long lines
            if len(line) > 100:
                self.add("info", f"Line too long ({len(line)} chars)", i, category="style")
            # Tab characters
            if "\t" in line:
                self.add("info", "Tab character detected (use spaces)", i, category="style")

def review_file(path):
    """Review a single Python file."""
    try:
        with open(path, "r") as f:
            source = f.read()
    except Exception as e:
        return [{"severity": "error", "msg": f"Cannot read: {e}", "file": path, "category": "io"}]

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return [{"severity": "error", "msg": f"Syntax error: {e}", "line": e.lineno or 0, "file": path, "category": "syntax"}]

    reviewer = CodeReviewer(source, filename=path)
    reviewer.visit(tree)
    reviewer.check_style()

    summary = {
        "file": path,
        "lines": len(reviewer.lines),
        "functions": reviewer.func_count,
        "classes": reviewer.class_count,
        "issues": reviewer.issues,
    }
    return [summary]

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Automated code review for Python files")
    parser.add_argument("paths", nargs="+", help="Files or directories to review")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--min-severity", choices=["error", "warning", "info"], default="info", help="Minimum severity")
    parser.add_argument("-r", "--recursive", action="store_true", help="Recursive directory scan")
    args = parser.parse_args()

    files = []
    for p in args.paths:
        path = Path(p)
        if path.is_file() and path.suffix == ".py":
            files.append(str(path))
        elif path.is_dir():
            pattern = "**/*.py" if args.recursive else "*.py"
            files.extend(str(f) for f in path.glob(pattern))

    if not files:
        print("No Python files found.")
        return

    all_reviews = []
    total_issues = {"error": 0, "warning": 0, "info": 0}
    for f in sorted(files):
        results = review_file(f)
        summary = results[0]
        all_reviews.append(summary)
        for issue in summary["issues"]:
            total_issues[issue["severity"]] += 1
        if not args.json:
            sev_map = {"error": "✗", "warning": "⚠", "info": "ℹ"}
            for issue in summary["issues"]:
                if issue["severity"] in ("error", "warning") or args.min_severity == "info":
                    print(f"{sev_map[issue['severity']]} {issue['file']}:{issue['line']}  {issue['msg']}")
            print(f"  → {summary['file']}: {len(summary['issues'])} issues ({summary['functions']} fn, {summary['classes']} cls)")

    if args.json:
        print(json.dumps(all_reviews, indent=2))
    else:
        print(f"\nTotal: {total_issues['error']} errors, {total_issues['warning']} warnings, {total_issues['info']} info")

if __name__ == "__main__":
    main()
