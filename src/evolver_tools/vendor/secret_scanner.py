#!/usr/bin/env python3
"""secret-scanner — Find hardcoded secrets, tokens, and credentials in code."""
import os, sys, re, json
from pathlib import Path
from collections import defaultdict

TOOL_META = {
    "name": "secret-scanner",
    "desc": "Find hardcoded secrets, tokens, and credentials in code",
    "func": "main",
}

# Pattern definitions
PATTERNS = [
    ("AWS Access Key", r"(?i)AKIA[0-9A-Z]{16}"),
    ("AWS Secret Key", r"(?i)(?<![a-zA-Z0-9+/=])[a-zA-Z0-9+/]{40}(?![a-zA-Z0-9+/=])", {"file_glob": "*.py,*.js,*.ts,*.yml,*.yaml,*.json,*.env,*"}),
    ("GitHub Token", r"(?i)(?:ghp|gho|ghu|ghs|ghr)_[a-zA-Z0-9]{36}"),
    ("GitLab Token", r"(?i)glpat-[a-zA-Z0-9\-]{20,30}"),
    ("Slack Token", r"(?i)xox[baprs]-[0-9a-zA-Z\-]{10,}"),
    ("Slack Webhook", r"https://hooks\.slack\.com/services/[A-Za-z0-9/]{40,}"),
    ("Generic API Key", r"(?i)(?:api[_-]?key|apikey|api[_-]?secret|secret[_-]?key)\s*[:=]\s*['\"][a-zA-Z0-9_\-\.]{16,}['\"]"),
    ("Password", r"(?i)(?:password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{4,}['\"]"),
    ("JWT Token", r"eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}"),
    ("Private Key Header", r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
    ("Heroku API Key", r"(?i)[hH][eE][rR][oO][kK][uU].*[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}"),
    ("Google OAuth", r"(?i)[0-9]+-[0-9a-zA-Z_]{32}\.apps\.googleusercontent\.com"),
    ("Telegram Bot Token", r"[0-9]{8,10}:[a-zA-Z0-9_-]{35}"),
    ("Docker Config Auth", r"(?i)(?:auths|auth)\s*:\s*\{\s*\"https://index\.docker\.io/v1/"),
    ("npm/.npmrc _auth", r"(?i)_auth\s*=\s*[a-zA-Z0-9+/=]{20,}"),
    ("Connection String", r"(?i)(?:mongodb|postgres|mysql|redis)://[^\s'\"]+:[^\s'\"@]+@"),
    (".env SENSITIVE", r"(?i)^(?:SECRET|TOKEN|KEY|PASSWORD|PASS|API_KEY|ACCESS_KEY|SECRET_KEY)\s*="),
]

IGNORE_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", "env",
               "dist", "build", ".egg-info", ".tox", ".mypy_cache", ".pytest_cache",
               "target", "vendor", ".bundle", ".next", ".nuxt"}
IGNORE_EXTS = {".pyc", ".pyo", ".so", ".dll", ".dylib", ".exe", ".bin",
               ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ico", ".svg",
               ".woff", ".woff2", ".ttf", ".eot", ".pdf", ".zip", ".tar",
               ".gz", ".bz2", ".7z", ".rar", ".o", ".a", ".lib", ".obj"}

def scan_file(path, context_lines=0):
    """Scan a single file for secrets."""
    findings = []
    try:
        with open(path, "r", errors="replace") as f:
            content = f.read()
    except (IOError, OSError):
        return findings

    lines = content.split("\n")
    for name, pattern, *opts in PATTERNS:
        ext_filter = None
        if opts:
            ext_filter = opts[0].get("file_glob", "")
            # Simple extension check
            if ext_filter:
                exts = [g.replace("*.", "").strip() for g in ext_filter.split(",")]
                ext = Path(path).suffix.lower()
                if ext not in exts and "*" not in ext_filter:
                    continue

        try:
            for match in re.finditer(pattern, content):
                # Find line number
                line_no = content[:match.start()].count("\n") + 1
                if line_no > len(lines):
                    continue
                findings.append({
                    "type": name,
                    "file": path,
                    "line": line_no,
                    "match": match.group()[:60],
                    "context": lines[line_no - 1].strip() if context_lines else "",
                })
        except re.error:
            continue

    return findings

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Find hardcoded secrets in code")
    parser.add_argument("paths", nargs="+", help="Files or directories to scan")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("-c", "--context", type=int, default=0, help="Context lines")
    parser.add_argument("-r", "--recursive", action="store_true", help="Recursive scan")
    parser.add_argument("-q", "--quiet", action="store_true", help="Only show findings (no summary)")
    parser.add_argument("--list-patterns", action="store_true", help="List available patterns")
    args = parser.parse_args()

    if args.list_patterns:
        print("Available scan patterns:")
        for name, pat in PATTERNS:
            print(f"  {name:25s} {pat[:50]}")
        return

    files = []
    for p in args.paths:
        path = Path(p)
        if path.is_file():
            files.append(str(path))
        elif path.is_dir():
            for f in path.rglob("*") if args.recursive else path.glob("*"):
                if f.is_file():
                    # Skip ignored dirs
                    rel = f.relative_to(path)
                    if any(part in IGNORE_DIRS for part in rel.parts):
                        continue
                    if f.suffix.lower() in IGNORE_EXTS:
                        continue
                    files.append(str(f))

    all_findings = []
    for f in sorted(files):
        findings = scan_file(f, context_lines=args.context)
        all_findings.extend(findings)
        if findings and not args.quiet:
            for finding in findings:
                indicator = "\033[91m!\033[0m"  # red
                print(f"{indicator} {finding['type']:20s} {finding['file']}:{finding['line']}")
                print(f"    {finding['match']}")

    if args.json:
        print(json.dumps(all_findings, indent=2))
    elif not args.quiet:
        by_type = defaultdict(int)
        for f in all_findings:
            by_type[f["type"]] += 1
        print(f"\nScanned: {len(files)} files")
        print(f"Findings: {len(all_findings)}")
        for t, c in sorted(by_type.items()):
            print(f"  {t}: {c}")

if __name__ == "__main__":
    main()
