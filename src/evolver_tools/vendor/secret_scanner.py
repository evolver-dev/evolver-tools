#!/usr/bin/env python3
"""secret-scanner — Scan files for potential secrets (API keys, tokens, passwords)."""
import os
import re
import sys

TOOL_META = {
    "name": "secret-scanner",
    "func": "main",
    "desc": "Scan files for secrets/API keys/tokens. Usage: secret-scanner [path]",
}

PATTERNS = [
    (r"(?i)api[_-]?key\s*[=:]\s*['\"][A-Za-z0-9_\-]{16,}['\"]", "API Key"),
    (r"(?i)secret\s*[=:]\s*['\"][A-Za-z0-9_\-]{16,}['\"]", "Secret"),
    (r"(?i)token\s*[=:]\s*['\"][A-Za-z0-9_\-\.]{16,}['\"]", "Token"),
    (r"(?i)password\s*[=:]\s*['\"][^'\"]{6,}['\"]", "Password"),
    (r"(?i)sk-[A-Za-z0-9]{20,}", "OpenAI API Key"),
    (r"(?i)ghp_[A-Za-z0-9]{36}", "GitHub Token"),
    (r"(?i)gho_[A-Za-z0-9]{36}", "GitHub OAuth Token"),
    (r"(?i)ghu_[A-Za-z0-9]{36}", "GitHub User Token"),
    (r"(?i)AKIA[0-9A-Z]{16}", "AWS Access Key"),
    (r"(?i)-----BEGIN (RSA |EC )?PRIVATE KEY-----", "Private Key"),
    (r"(?i)xox[baprs]-[A-Za-z0-9\-]{10,}", "Slack Token"),
    (r"(?i)eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}", "JWT Token"),
    (r"(?i)pk_live_[A-Za-z0-9]{24}", "Stripe Live Key"),
    (r"(?i)sk_live_[A-Za-z0-9]{24}", "Stripe Secret Key"),
    (r"(?i)AIza[0-9A-Za-z\-_]{35}", "Google API Key"),
]

IGNORE_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", ".tox", "dist", "build", ".egg-info"}

def scan_file(filepath):
    findings = []
    try:
        with open(filepath, "r", errors="ignore") as f:
            content = f.read()
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            for pattern, label in PATTERNS:
                if re.search(pattern, line):
                    truncated = line.strip()[:80]
                    findings.append((filepath, i, label, truncated))
                    break
    except Exception:
        pass
    return findings

def scan_dir(root_path):
    findings = []
    for root, dirs, files in os.walk(root_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in (".pyc", ".pyo", ".so", ".dll", ".dylib", ".png", ".jpg", ".gif", ".zip", ".tar", ".gz"):
                continue
            filepath = os.path.join(root, f)
            findings.extend(scan_file(filepath))
    return findings

def main():
    args = sys.argv[1:]
    path = args[0] if args else "."
    path = os.path.abspath(path)
    print(f"Scanning: {path}")
    findings = []
    if os.path.isfile(path):
        findings = scan_file(path)
    else:
        findings = scan_dir(path)
    if not findings:
        print("No secrets found.")
        return
    print(f"Found {len(findings)} potential secrets:\n")
    for filepath, line_num, label, snippet in findings:
        rel = os.path.relpath(filepath, os.getcwd())
        print(f"  [{label}] {rel}:{line_num}")
        print(f"    {snippet}")
        print()

if __name__ == "__main__":
    main()
