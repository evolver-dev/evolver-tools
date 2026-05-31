#!/usr/bin/env python3
"""code-stats — Code line statistics by language."""
import os
import sys

TOOL_META = {
    "name": "code-stats",
    "func": "main",
    "desc": "Count lines of code by language. Usage: code-stats [path]",
}

EXT_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript React",
    ".jsx": "JavaScript React",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".rb": "Ruby",
    ".php": "PHP",
    ".c": "C",
    ".h": "C Header",
    ".cpp": "C++",
    ".hpp": "C++ Header",
    ".cs": "C#",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".scala": "Scala",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".fish": "Shell",
    ".ps1": "PowerShell",
    ".sql": "SQL",
    ".r": "R",
    ".m": "Objective-C",
    ".lua": "Lua",
    ".pl": "Perl",
    ".pm": "Perl",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".erl": "Erlang",
    ".hs": "Haskell",
    ".clj": "Clojure",
    ".cljs": "ClojureScript",
    ".dart": "Dart",
    ".md": "Markdown",
    ".rst": "reStructuredText",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "Sass",
    ".less": "Less",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".xml": "XML",
    ".tex": "LaTeX",
    ".dockerfile": "Dockerfile",
    ".makefile": "Makefile",
}

IGNORE_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", ".tox", "dist", "build", ".egg-info", ".mypy_cache", ".pytest_cache", ".ruff_cache", "target", "vendor"}

def count_lines(filepath):
    try:
        with open(filepath, "rb") as f:
            data = f.read()
        lines = data.count(b"\n")
        if data and not data.endswith(b"\n"):
            lines += 1
        return lines
    except Exception:
        return 0

def main():
    args = sys.argv[1:]
    path = args[0] if args else "."
    path = os.path.abspath(path)
    stats = {}
    total_files = 0
    total_lines = 0
    if os.path.isfile(path):
        ext = os.path.splitext(path)[1].lower()
        lang = EXT_MAP.get(ext, "Unknown")
        lines = count_lines(path)
        stats[lang] = {"files": 1, "lines": lines}
        total_files = 1
        total_lines = lines
    else:
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                lang = EXT_MAP.get(ext)
                if not lang:
                    # Check for extensionless files
                    if f.lower() in ("dockerfile",):
                        lang = "Dockerfile"
                    elif f.lower() in ("makefile", "gnumakefile"):
                        lang = "Makefile"
                    else:
                        continue
                filepath = os.path.join(root, f)
                lines = count_lines(filepath)
                if lang not in stats:
                    stats[lang] = {"files": 0, "lines": 0}
                stats[lang]["files"] += 1
                stats[lang]["lines"] += lines
                total_files += 1
                total_lines += lines
    if not stats:
        print(f"No code files found in {path}")
        return
    # Display
    name_width = max(len(n) for n in stats.keys())
    sorted_stats = sorted(stats.items(), key=lambda x: -x[1]["lines"])
    print(f"{'Language':<{name_width}}  {'Files':>6}  {'Lines':>8}  {'%':>5}")
    print("-" * (name_width + 24))
    for lang, info in sorted_stats:
        pct = info["lines"] / total_lines * 100 if total_lines else 0
        print(f"{lang:<{name_width}}  {info['files']:>6}  {info['lines']:>8}  {pct:>4.1f}%")
    print("-" * (name_width + 24))
    print(f"{'TOTAL':<{name_width}}  {total_files:>6}  {total_lines:>8}")

if __name__ == "__main__":
    main()
