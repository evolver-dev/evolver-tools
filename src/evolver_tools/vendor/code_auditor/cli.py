"""
code-auditor CLI — complexity, security, style, and dependency analysis.

All analysis uses only Python stdlib modules (ast, tokenize, etc.).
"""

from __future__ import annotations

import ast
import os
import re
import sys
import tokenize
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ────────────────────────────────────────────────────────────
# Colour / terminal helpers
# ────────────────────────────────────────────────────────────

_COLORS = {
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "cyan": "\033[96m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "reset": "\033[0m",
}


def _c(code: str, text: str) -> str:
    """Wrap *text* in ANSI colour *code* if stdout is a TTY."""
    if sys.stdout.isatty() and code in _COLORS:
        return f"{_COLORS[code]}{text}{_COLORS['reset']}"
    return text


def _header(title: str) -> str:
    sep = "━" * 54
    return f"\n{_c('cyan', sep)}\n{_c('bold', title)}\n{_c('cyan', sep)}"


def _subheader(title: str) -> str:
    return f"\n{_c('cyan', '[' + title + ']')} {'─' * (52 - len(title))}"


# ────────────────────────────────────────────────────────────
# Utility
# ────────────────────────────────────────────────────────────


def _walk_py_files(path: str) -> List[Path]:
    """Return a sorted list of .py files under *path* (or the file itself)."""
    p = Path(path)
    if p.is_file():
        if p.suffix == ".py":
            return [p]
        return []
    if p.is_dir():
        return sorted(p.rglob("*.py"))
    return []


def _read_source(path: Path) -> Tuple[str, List[str]]:
    """Read *path* and return (source_text, lines_list)."""
    text = path.read_text(encoding="utf-8", errors="replace")
    return text, text.splitlines()


# ════════════════════════════════════════════════════════════
# 1. CYCLOMATIC COMPLEXITY
# ════════════════════════════════════════════════════════════


class ComplexityVisitor(ast.NodeVisitor):
    """Compute McCabe cyclomatic complexity per function / method."""

    def __init__(self) -> None:
        self.complexities: List[Tuple[str, str, int, int]] = []
        # (name, kind, lineno, score)

    def _score(self, node: ast.AST) -> int:
        """Recursively count decision points."""
        s = 1  # base
        for child in ast.walk(node):
            if isinstance(
                child,
                (
                    ast.If,
                    ast.While,
                    ast.For,
                    ast.AsyncFor,
                    ast.ExceptHandler,
                ),
            ):
                s += 1
            elif isinstance(child, ast.BoolOp):
                s += len(child.values) - 1
            elif isinstance(child, ast.With):
                s += 1
            elif isinstance(child, ast.Assert):
                s += 1
            elif isinstance(child, (ast.And, ast.Or)):
                s += 1
            elif isinstance(child, ast.comprehension):
                s += 1 + len(child.ifs)
        return s

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.complexities.append(
            (node.name, "function", node.lineno or 0, self._score(node))
        )
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.complexities.append(
            (node.name, "async function", node.lineno or 0, self._score(node))
        )
        self.generic_visit(node)


def analyze_complexity(source: str, _lines: Optional[List[str]] = None
                      ) -> List[Dict[str, Any]]:
    """Return a list of complexity results.

    Each result dict::

        {"name": str, "kind": str, "line": int, "complexity": int, "ok": bool}
    """
    results: List[Dict[str, Any]] = []
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [{"name": f"<syntax error: {exc}>", "kind": "error",
                 "line": exc.lineno or 0, "complexity": 0, "ok": False}]

    visitor = ComplexityVisitor()
    visitor.visit(tree)
    for name, kind, lineno, score in visitor.complexities:
        results.append({
            "name": name,
            "kind": kind,
            "line": lineno,
            "complexity": score,
            "ok": score <= 10,
        })
    return results


def _format_complexity(results: List[Dict[str, Any]], path: str) -> str:
    out = [_subheader("COMPLEXITY")]
    if not results:
        out.append(f"  {_c('yellow', 'No functions found or file unparseable.')}")
        return "\n".join(out)

    for r in results:
        if r["kind"] == "error":
            out.append(f"  {_c('red', r['name'])}")
            continue
        label = _c("green", "OK") if r["ok"] else _c("yellow", "WARN")
        out.append(
            f"  {_c('bold', r['name'])} "
            f"(line {r['line']})  "
            f"complexity: {r['complexity']}  {label}"
        )
    return "\n".join(out)


# ════════════════════════════════════════════════════════════
# 2. SECURITY AUDIT
# ════════════════════════════════════════════════════════════

# Patterns that flag security concerns in source lines.
_SECURITY_PATTERNS: List[Tuple[str, str, str]] = [
    # (pattern_type, description, regex)
    ("eval", "Use of 'eval()' detected", r"\beval\s*\("),
    ("exec", "Use of 'exec()' detected", r"\bexec\s*\("),
    ("subprocess_shell", "subprocess with shell=True detected",
     r"subprocess\.\w+\(.*shell\s*=\s*True"),
    ("pickle_unsafe", "Unsafe pickle.loads/deprecated pattern",
     r"pickle\.(loads?|Unpickler)\s*\("),
    ("hardcoded_password", "Potential hardcoded password",
     r"(?:password|passwd|pwd|secret)\s*[=:]\s*['\"][^'\"]+['\"]"),
    ("sql_injection", "Possible SQL injection (string concatenation in query)",
     r"(?:execute|cursor\.execute)\s*\(\s*(?:f['\"]|['\"]\s*\+\s*|['\"].*\{)"),
    ("yaml_unsafe", "Unsafe yaml.load() without Loader",
     r"yaml\.load\s*\(\s*(?!.*(?:Loader|SafeLoader))"),
    ("mktemp", "Use of insecure mktemp()", r"\bmktemp\s*\("),
    ("assert_not_secure", "assert statement used (discarded with -O)",
     r"^\s*assert\s+"),
    ("input_unsafe", "Use of builtin input() in Python 2 style",
     r"\binput\s*\(\s*\)"),
    ("request_verify_false", "requests with verify=False",
     r"verify\s*=\s*False"),
]

# Allowlist for naming-based bypass (e.g. test files often use assert)
_SECURITY_IGNORE_PATTERNS = [
    r"def test_",
    r"class Test",
]


def analyze_security(source: str, lines: List[str]) -> List[Dict[str, Any]]:
    """Return a list of security findings.

    Each result dict::

        {"line": int, "severity": str, "message": str, "code": str}
    """
    results: List[Dict[str, Any]] = []
    line_iter = iter(lines)

    for lineno, raw_line in enumerate(lines, 1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        for pattern_type, desc, regex in _SECURITY_PATTERNS:
            if re.search(regex, stripped):
                # Skip if line looks like a test or definition
                if any(re.match(ig, stripped) for ig in _SECURITY_IGNORE_PATTERNS):
                    continue
                results.append({
                    "line": lineno,
                    "severity": "WARNING",
                    "message": desc,
                    "code": stripped.strip(),
                })
                break  # one finding per line
    return results


def _format_security(results: List[Dict[str, Any]], path: str) -> str:
    out = [_subheader("SECURITY")]
    if not results:
        out.append(f"  {_c('green', 'No security issues found.')}")
        return "\n".join(out)

    for r in results:
        out.append(
            f"  Line {r['line']:>4}:  "
            f"{_c('red', r['severity'])}  "
            f"{r['message']}"
        )
        out.append(f"          {_c('dim', r['code'])}")
    return "\n".join(out)


# ════════════════════════════════════════════════════════════
# 3. STYLE CHECK
# ════════════════════════════════════════════════════════════


def _check_line_length(lines: List[str], max_len: int = 79
                       ) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    for i, line in enumerate(lines, 1):
        # Ignore shebang and long string literals
        if i == 1 and line.startswith("#!"):
            continue
        if len(line) > max_len:
            findings.append({
                "line": i,
                "severity": "STYLE",
                "message": f"Line exceeds {max_len} characters ({len(line)})",
                "code": line.rstrip(),
            })
    return findings


def _check_trailing_whitespace(lines: List[str]) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    for i, line in enumerate(lines, 1):
        if line != line.rstrip() and not line.startswith("#"):
            findings.append({
                "line": i,
                "severity": "STYLE",
                "message": "Trailing whitespace detected",
                "code": repr(line),
            })
    return findings


def _check_naming(source: str, lines: List[str]) -> List[Dict[str, Any]]:
    """Check naming conventions via AST."""

    findings: List[Dict[str, Any]] = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return findings

    function_pattern = re.compile(r"^[a-z_][a-z0-9_]*$")
    class_pattern = re.compile(r"^[A-Z][a-zA-Z0-9]*$")
    constant_pattern = re.compile(r"^[A-Z][A-Z0-9_]*$")

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if not function_pattern.match(node.name) and not node.name.startswith("__"):
                findings.append({
                    "line": node.lineno or 0,
                    "severity": "STYLE",
                    "message": f"Function '{node.name}' should use snake_case",
                    "code": node.name,
                })
        elif isinstance(node, ast.ClassDef):
            if not class_pattern.match(node.name):
                findings.append({
                    "line": node.lineno or 0,
                    "severity": "STYLE",
                    "message": f"Class '{node.name}' should use PascalCase",
                    "code": node.name,
                })
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    name = target.id
                    if name.isupper() and len(name) > 1:
                        if not constant_pattern.match(name):
                            findings.append({
                                "line": node.lineno or 0,
                                "severity": "STYLE",
                                "message": f"Constant '{name}' should be ALL_CAPS",
                                "code": name,
                            })

    return findings


def _check_docstrings(source: str, lines: List[str]) -> List[Dict[str, Any]]:
    """Check that every module/function/class has a docstring."""
    findings: List[Dict[str, Any]] = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return findings

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            # Skip dunder methods and private helpers
            if isinstance(node, ast.FunctionDef) and node.name.startswith("__"):
                continue
            if (not ast.get_docstring(node)
                    and not getattr(node, "body", None)):
                # No body = abstract / protocol stub
                continue
            if not ast.get_docstring(node):
                kind = "class" if isinstance(node, ast.ClassDef) else "function"
                findings.append({
                    "line": node.lineno or 0,
                    "severity": "STYLE",
                    "message": f"Missing docstring for {kind} '{node.name}'",
                    "code": node.name,
                })

    # Module-level docstring
    if not ast.get_docstring(tree):
        findings.insert(0, {
            "line": 1,
            "severity": "STYLE",
            "message": "Missing module-level docstring",
            "code": "(module)",
        })

    return findings


def _check_bad_indentation(lines: List[str]) -> List[Dict[str, Any]]:
    """Flag lines that mix tabs and spaces inconsistently."""
    findings: List[Dict[str, Any]] = []
    for i, line in enumerate(lines, 1):
        if "\t" in line:
            findings.append({
                "line": i,
                "severity": "STYLE",
                "message": "Tab character detected (use spaces)",
                "code": repr(line),
            })
    return findings


def analyze_style(source: str, lines: List[str]) -> List[Dict[str, Any]]:
    """Run all style checks and return a combined list of findings."""
    findings: List[Dict[str, Any]] = []
    findings.extend(_check_line_length(lines))
    findings.extend(_check_trailing_whitespace(lines))
    findings.extend(_check_naming(source, lines))
    findings.extend(_check_docstrings(source, lines))
    findings.extend(_check_bad_indentation(lines))
    return findings


def _format_style(results: List[Dict[str, Any]], path: str) -> str:
    out = [_subheader("STYLE")]
    if not results:
        out.append(f"  {_c('green', 'Style looks good.')}")
        return "\n".join(out)

    for r in results:
        out.append(
            f"  Line {r['line']:>4}:  "
            f"{_c('yellow', r['severity'])}  "
            f"{r['message']}"
        )
        out.append(f"          {_c('dim', r['code'])}")
    return "\n".join(out)


# ════════════════════════════════════════════════════════════
# 4. DEPENDENCY ANALYSIS
# ════════════════════════════════════════════════════════════

# Known stdlib module prefixes — comprehensive list.
_STDLIB_MODULES: set[str] = {
    "abc", "aifc", "argparse", "array", "ast", "asynchat", "asyncio",
    "asyncore", "atexit", "audioop", "base64", "bdb", "binascii",
    "binhex", "bisect", "builtins", "bz2", "calendar", "cgi",
    "cgitb", "chunk", "cmath", "cmd", "code", "codecs", "codeop",
    "collections", "colorsys", "compileall", "concurrent", "configparser",
    "contextlib", "contextvars", "copy", "copyreg", "cProfile",
    "crypt", "csv", "ctypes", "curses", "dataclasses", "datetime",
    "dbm", "decimal", "difflib", "dis", "distutils", "doctest",
    "email", "encodings", "enum", "errno", "faulthandler", "fcntl",
    "filecmp", "fileinput", "fnmatch", "fractions", "ftplib",
    "functools", "gc", "getopt", "getpass", "gettext", "glob",
    "graphlib", "grp", "gzip", "hashlib", "heapq", "hmac", "html",
    "http", "idlelib", "imaplib", "imghdr", "imp", "importlib",
    "inspect", "io", "ipaddress", "itertools", "json", "keyword",
    "lib2to3", "linecache", "locale", "logging", "lzma", "mailbox",
    "mailcap", "marshal", "math", "mimetypes", "mmap", "modulefinder",
    "multiprocessing", "netrc", "nis", "nntplib", "numbers", "operator",
    "optparse", "os", "ossaudiodev", "pathlib", "pdb", "pickle",
    "pickletools", "pipes", "pkgutil", "platform", "plistlib",
    "poplib", "posix", "posixpath", "pprint", "profile", "pstats",
    "pty", "pwd", "py_compile", "pyclbr", "pydoc", "queue", "quopri",
    "random", "re", "readline", "reprlib", "resource", "rlcompleter",
    "runpy", "sched", "secrets", "select", "selectors", "shelve",
    "shlex", "shutil", "signal", "site", "smtpd", "smtplib",
    "sndhdr", "socket", "socketserver", "sqlite3", "ssl", "stat",
    "statistics", "string", "stringprep", "struct", "subprocess",
    "sunau", "symtable", "sys", "sysconfig", "syslog", "tabnanny",
    "tarfile", "telnetlib", "tempfile", "termios", "test", "textwrap",
    "threading", "time", "timeit", "tkinter", "token", "tokenize",
    "tomllib", "trace", "traceback", "tracemalloc", "tty",
    "turtle", "turtledemo", "types", "typing", "unicodedata",
    "unittest", "urllib", "uu", "uuid", "venv", "warnings", "wave",
    "weakref", "webbrowser", "winreg", "winsound", "wsgiref",
    "xdrlib", "xml", "xmlrpc", "zipapp", "zipfile", "zipimport",
    "zlib", "__future__",
}

# Common third-party packages that are well-known
_KNOWN_THIRD_PARTY: set[str] = {
    "numpy", "pandas", "requests", "flask", "django", "pytest",
    "torch", "tensorflow", "scipy", "matplotlib", "seaborn",
    "sqlalchemy", "click", "rich", "typer", "fastapi", "pydantic",
    "boto3", "redis", "celery", "scikit_learn", "sklearn",
    "beautifulsoup4", "bs4", "lxml", "pyyaml", "yaml",
    "colorama", "tqdm", "jinja2", "pillow", "PIL", "psutil",
    "protobuf", "grpcio", "aiohttp", "websockets", "cryptography",
    "paramiko", "docker", "kubernetes", "prometheus_client",
    "opentelemetry", "httpx", "jwt", "pymongo", "asyncpg",
    "psycopg2", "mypy", "black", "isort", "flake8", "pylint",
    "coverage", "sphinx", "mypy_extensions",
}


def _categorize_import(name: str) -> str:
    """Return 'stdlib', 'third-party', or 'local' for a top-level module name."""
    base = name.split(".")[0]
    if base in _STDLIB_MODULES:
        return "stdlib"
    if base in _KNOWN_THIRD_PARTY:
        return "third-party"
    return "local"


def analyze_deps(source: str, _lines: Optional[List[str]] = None
                 ) -> Dict[str, Dict[str, List[str]]]:
    """Scan imports and categorise them.

    Returns::

        {"stdlib": {"os": [...alias...]},
         "third_party": {...},
         "local": {...}}
    """
    categorized: Dict[str, Dict[str, List[str]]] = {
        "stdlib": {},
        "third-party": {},
        "local": {},
    }
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return categorized

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                cat = _categorize_import(alias.name)
                asname = alias.asname or ""
                if alias.name not in categorized[cat]:
                    categorized[cat][alias.name] = []
                if asname and asname != alias.name:
                    categorized[cat][alias.name].append(asname)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            for alias in node.names:
                full = f"{mod}.{alias.name}" if mod else alias.name
                cat = _categorize_import(full)
                asname = alias.asname or ""
                if full not in categorized[cat]:
                    categorized[cat][full] = []
                if asname and asname != alias.name:
                    categorized[cat][full].append(asname)

    return categorized


def _format_deps(result: Dict[str, Dict[str, List[str]]]) -> str:
    out = [_subheader("DEPENDENCIES")]
    has_any = False
    for cat_name, display_name in [
        ("stdlib", "stdlib"),
        ("third-party", "third-party"),
        ("local", "local"),
    ]:
        items = result.get(cat_name, {})
        if not items:
            continue
        has_any = True
        lines_out: List[str] = []
        for mod_name, aliases in items.items():
            if aliases:
                lines_out.append(f"{mod_name} as {', '.join(aliases)}")
            else:
                lines_out.append(mod_name)
        colour = {"stdlib": "green", "third-party": "yellow", "local": "cyan"}.get(
            cat_name, "reset"
        )
        out.append(f"  {_c(colour, cat_name)}: {', '.join(sorted(lines_out))}")

    if not has_any:
        out.append(f"  {_c('yellow', 'No imports found.')}")
    return "\n".join(out)


# ════════════════════════════════════════════════════════════
# 5. ALL-IN-ONE RUNNER
# ════════════════════════════════════════════════════════════


def run_all(source: str, lines: List[str], path: str) -> str:
    """Run all checks and return a formatted report."""
    parts: List[str] = []
    parts.append(_header(f"code-auditor — all checks  [{path}]"))

    # Complexity
    cx = analyze_complexity(source, lines)
    parts.append(_format_complexity(cx, path))

    # Security
    sec = analyze_security(source, lines)
    parts.append(_format_security(sec, path))

    # Style
    sty = analyze_style(source, lines)
    parts.append(_format_style(sty, path))

    # Dependencies
    deps = analyze_deps(source, lines)
    parts.append(_format_deps(deps))

    # Summary counts
    n_sec = len(sec)
    n_sty = len(sty)
    n_high_cx = sum(1 for r in cx if not r.get("ok", True))
    total_warn = n_sec + n_sty + n_high_cx

    parts.append(_header("Summary"))
    if total_warn == 0:
        parts.append(f"  {_c('green', 'All checks passed.  ✨')}")
    else:
        if n_sec:
            parts.append(f"  {_c('red', f'Security issues: {n_sec}')}")
        if n_sty:
            parts.append(f"  {_c('yellow', f'Style issues: {n_sty}')}")
        if n_high_cx:
            parts.append(f"  {_c('yellow', f'High complexity: {n_high_cx}')}")
    parts.append(_c("cyan", "━" * 54) + "\n")

    return "\n".join(parts)


# ════════════════════════════════════════════════════════════
# 6. SINGLE-CHECK RUNNERS (format output for CLI)
# ════════════════════════════════════════════════════════════


def _run_single_check(source: str, lines: List[str], path: str,
                      check: str) -> str:
    """Dispatch to the right checker and return formatted output."""
    parts: List[str] = []
    parts.append(_header(f"code-auditor — {check}  [{path}]"))

    if check == "complexity":
        parts.append(_format_complexity(analyze_complexity(source, lines), path))
    elif check == "security":
        parts.append(_format_security(analyze_security(source, lines), path))
    elif check == "style":
        parts.append(_format_style(analyze_style(source, lines), path))
    elif check == "deps":
        parts.append(_format_deps(analyze_deps(source, lines)))
    else:
        parts.append(f"  {_c('red', f'Unknown check: {check}')}")

    parts.append("")
    return "\n".join(parts)


def _check_exit_code(results: List[Dict[str, Any]], check_type: str) -> int:
    """Determine exit code: 0 = clean, 1 = style/complexity warn, 2 = security."""
    for r in results:
        if r.get("severity") == "WARNING" and check_type == "security":
            return 2
        if not r.get("ok", True):
            return 1
    return 0


# ════════════════════════════════════════════════════════════
# 7. TUI MODE (curses-based)
# ════════════════════════════════════════════════════════════


def _run_tui() -> int:
    """Interactive curses-based TUI for code-auditor."""
    import curses
    import textwrap

    # ── data ─────────────────────────────────────────────
    files: List[Path] = []
    current_results: List[Dict[str, Any]] = []
    current_check = "all"
    status_message = "Press ? for help"

    def _load_files(base: str) -> None:
        nonlocal files
        files.clear()
        p = Path(base).expanduser().resolve()
        if p.is_file() and p.suffix == ".py":
            files.append(p)
        elif p.is_dir():
            files.extend(sorted(p.rglob("*.py")))

    def _run_on_files(check: str) -> List[Dict[str, Any]]:
        nonlocal current_results
        combined: List[Dict[str, Any]] = []
        for f in files:
            try:
                src, lines = _read_source(f)
                if check in ("complexity", "all"):
                    for r in analyze_complexity(src, lines):
                        r["_file"] = str(f)
                        combined.append(r)
                if check in ("security", "all"):
                    for r in analyze_security(src, lines):
                        r["_file"] = str(f)
                        combined.append(r)
                if check in ("style", "all"):
                    for r in analyze_style(src, lines):
                        r["_file"] = str(f)
                        combined.append(r)
            except Exception:
                pass
        current_results = combined
        return combined

    def _draw(stdscr: Any) -> int:
        nonlocal status_message
        curses.curs_set(0)
        curses.use_default_colors()
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        exit_code = 0

        # Setup color pairs
        curses.init_pair(1, curses.COLOR_RED, -1)
        curses.init_pair(2, curses.COLOR_YELLOW, -1)
        curses.init_pair(3, curses.COLOR_GREEN, -1)
        curses.init_pair(4, curses.COLOR_CYAN, -1)
        RED, YELLOW, GREEN, CYAN = 1, 2, 3, 4

        while True:
            stdscr.clear()

            # ── header ──
            hdr = f" code-auditor TUI — {current_check}  |  {len(files)} file(s)  |  {len(current_results)} finding(s) "
            stdscr.attron(curses.A_REVERSE | curses.A_BOLD)
            stdscr.addstr(0, 0, hdr.ljust(width - 1))
            stdscr.attroff(curses.A_REVERSE | curses.A_BOLD)

            # ── body ──
            row = 2
            max_row = height - 3

            if not files:
                stdscr.addstr(row, 2, "No files loaded. Press 'o' to open a file or directory.", YELLOW)
                row += 2

            for r in current_results[:max_row - 2]:
                if row >= max_row:
                    break
                fname = Path(r.get("_file", "")).name
                line = r.get("line", 0)
                msg = r.get("message", "")
                severity = r.get("severity", "")
                colour = RED if severity == "WARNING" else YELLOW
                label = f"[{fname}:{line}]"
                stdscr.addstr(row, 2, label, curses.A_DIM)
                col = len(label) + 4
                if col < width - 10:
                    stdscr.addstr(row, col, msg[: width - col - 4], colour)
                row += 1

            # ── status bar ──
            stdscr.attron(curses.A_REVERSE)
            status = status_message[: width - 2]
            stdscr.addstr(height - 1, 0, status.ljust(width - 1))
            stdscr.attroff(curses.A_REVERSE)

            # ── help popup ──
            def show_help() -> None:
                help_lines = [
                    "  KEY    ACTION",
                    "  ─────  ──────────────────────────────────",
                    "  q      Quit",
                    "  ?      Toggle this help",
                    "  o      Open file or directory",
                    "  r      Re-run current check",
                    "  1-5    Switch check: 1=all, 2=complexity,",
                    "         3=security, 4=style, 5=deps",
                    "  ↑/↓   Scroll (not yet implemented)",
                    "",
                    "  code-auditor analyzes .py files using",
                    "  only Python's standard library.",
                ]
                pop_h, pop_w = 16, 50
                pop_y = max(0, (height - pop_h) // 2)
                pop_x = max(0, (width - pop_w) // 2)
                for i, line in enumerate(help_lines):
                    stdscr.addstr(pop_y + i, pop_x, line.ljust(pop_w),
                                  curses.A_DIM)
                stdscr.refresh()

            show_help_visible = False

            while True:
                key = stdscr.getch()

                if key == ord("q"):
                    return exit_code

                elif key == ord("?"):
                    show_help_visible = not show_help_visible
                    if show_help_visible:
                        show_help()
                    break

                elif key == ord("o"):
                    curses.curs_set(1)
                    curses.echo()
                    stdscr.addstr(height - 1, 0, "Path: ".ljust(width - 1))
                    curses.doupdate()
                    path_input = stdscr.getstr(height - 1, 6, 60).decode(
                        "utf-8", errors="replace"
                    )
                    curses.noecho()
                    curses.curs_set(0)
                    if path_input.strip():
                        _load_files(path_input.strip())
                        _run_on_files(current_check)
                        status_message = f"Loaded {len(files)} file(s) from {path_input.strip()}"
                    break

                elif key == ord("r"):
                    _run_on_files(current_check)
                    status_message = f"Re-ran {current_check} — {len(current_results)} finding(s)"
                    break

                elif key == ord("1"):
                    current_check = "all"
                    _run_on_files(current_check)
                    status_message = f"Check: {current_check}"
                    break
                elif key == ord("2"):
                    current_check = "complexity"
                    _run_on_files(current_check)
                    status_message = f"Check: {current_check}"
                    break
                elif key == ord("3"):
                    current_check = "security"
                    _run_on_files(current_check)
                    status_message = f"Check: {current_check}"
                    break
                elif key == ord("4"):
                    current_check = "style"
                    _run_on_files(current_check)
                    status_message = f"Check: {current_check}"
                    break
                elif key == ord("5"):
                    current_check = "deps"
                    _run_on_files(current_check)
                    status_message = f"Check: {current_check}"
                    break

                elif key == ord("c"):
                    current_results.clear()
                    status_message = "Cleared results"
                    break

            # end inner loop
        # end outer loop

    try:
        return curses.wrapper(_draw)
    except Exception as exc:
        print(f"{_c('red', 'TUI error')}: {exc}", file=sys.stderr)
        return 1


# ════════════════════════════════════════════════════════════
# 8. MAIN ENTRY POINT
# ════════════════════════════════════════════════════════════


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point. Returns an exit code."""
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        print(
            _c("red", "Usage:") + " code-auditor <check> <path> [--tui]\n"
            "  Checks: complexity | security | style | deps | all\n"
            "  TUI:    code-auditor --tui",
            file=sys.stderr,
        )
        return 1

    # ── TUI mode ──
    if "--tui" in argv:
        return _run_tui()

    if len(argv) < 2:
        check = argv[0]
        if check in ("--help", "-h"):
            print(
                "Usage:\n"
                "  code-auditor complexity <file>\n"
                "  code-auditor security   <file/dir>\n"
                "  code-auditor style      <file/dir>\n"
                "  code-auditor deps       <file/dir>\n"
                "  code-auditor all        <file/dir>\n"
                "  code-auditor --tui\n"
            )
            return 0
        print(
            _c("red", "Error:") + " missing path argument.\n"
            "  Usage: code-auditor " + check + " <file|dir>",
            file=sys.stderr,
        )
        return 1

    check = argv[0]
    path = argv[1]

    # Validate check name
    valid_checks = {"complexity", "security", "style", "deps", "all"}
    if check not in valid_checks:
        print(
            _c("red", "Error:") + f" unknown check '{check}'.\n"
            f"  Valid: {', '.join(sorted(valid_checks))}",
            file=sys.stderr,
        )
        return 1

    # Gather files
    py_files = _walk_py_files(path)
    if not py_files:
        print(
            _c("red", "Error:") + f" no Python files found at '{path}'.",
            file=sys.stderr,
        )
        return 1

    overall_exit = 0
    for f in py_files:
        try:
            source, lines = _read_source(f)
        except Exception as exc:
            print(f"{_c('red', 'Error reading')} {f}: {exc}", file=sys.stderr)
            overall_exit = max(overall_exit, 1)
            continue

        if check == "all":
            report = run_all(source, lines, str(f))
            print(report)

            # Determine exit code
            sec = analyze_security(source, lines)
            sty = analyze_style(source, lines)
            cx = analyze_complexity(source, lines)
            if sec:
                overall_exit = max(overall_exit, 2)
            if sty or any(not r.get("ok", True) for r in cx):
                overall_exit = max(overall_exit, 1)
        else:
            report = _run_single_check(source, lines, str(f), check)
            print(report)

            results: List[Dict[str, Any]] = []
            if check == "complexity":
                results = analyze_complexity(source, lines)
                overall_exit = max(overall_exit, _check_exit_code(results, check))
            elif check == "security":
                results = analyze_security(source, lines)
                overall_exit = max(overall_exit, _check_exit_code(results, check))
            elif check == "style":
                results = analyze_style(source, lines)
                if results:
                    overall_exit = max(overall_exit, 1)
            elif check == "deps":
                pass  # deps never fail

    return overall_exit


if __name__ == "__main__":
    sys.exit(main())
