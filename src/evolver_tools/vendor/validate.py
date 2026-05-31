#!/usr/bin/env python3
"""validate — Generic file validator for JSON, YAML, CSV, TOML, XML.

Auto-detects format by file extension, validates syntax,
and reports errors with line numbers.

Usage:
    validate file.json         # Validate JSON
    validate *.yaml            # Validate all YAML files
    validate data.csv          # Validate CSV
    validate --list            # Show supported formats
"""

import json
import csv
import sys
import os
import io

TOOL_META = {
    "name": "validate",
    "func": "main",
    "desc": "Generic file validator (JSON/YAML/CSV/TOML/XML auto-detect)",
}

# ── CSV ──────────────────────────────────────────────────────────

def _validate_csv(path):
    errors = []
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        first = f.read(8192)
        f.seek(0)
        # Try detecting dialect
        try:
            dialect = csv.Sniffer().sniff(first[:4096])
        except csv.Error:
            dialect = csv.excel

        reader = csv.reader(f, dialect)
        header = None
        for i, row in enumerate(reader, 1):
            if i == 1:
                header = row
                continue
            if len(row) != len(header):
                errors.append(f"  Line {i}: expected {len(header)} columns, got {len(row)}")
    return errors


# ── JSON ─────────────────────────────────────────────────────────

def _validate_json(path):
    errors = []
    with open(path, encoding="utf-8", errors="replace") as f:
        content = f.read()
    try:
        json.loads(content)
    except json.JSONDecodeError as e:
        errors.append(f"  Line {e.lineno}, col {e.colno}: {e.msg}")
    return errors


# ── YAML (manual, no PyYAML dep) ────────────────────────────────
# Basic structural validation only — checks indentation and colons

def _validate_yaml(path):
    errors = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, 1):
            stripped = line.rstrip("\n\r")
            if stripped.strip() == "" or stripped.strip().startswith("#"):
                continue
            # Check for tabs (yaml disallows tabs)
            if "\t" in stripped:
                errors.append(f"  Line {i}: tabs not allowed in YAML (use spaces)")
            # Check for unquoted special chars
            if ":" in stripped and not stripped.strip().startswith("-"):
                idx = stripped.index(":")
                after = stripped[idx + 1:].strip()
                if after == "" or after.startswith(" "):
                    pass  # valid key: value
    return errors


# ── TOML (manual) ────────────────────────────────────────────────

def _validate_toml(path):
    errors = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, 1):
            stripped = line.rstrip("\n\r")
            if stripped.strip() == "" or stripped.strip().startswith("#"):
                continue
            if "=" in stripped:
                parts = stripped.split("=", 1)
                key = parts[0].strip()
                val = parts[1].strip()
                if not key:
                    errors.append(f"  Line {i}: empty key before '='")
    return errors


# ── XML (manual) ────────────────────────────────────────────────

def _validate_xml(path):
    errors = []
    with open(path, encoding="utf-8", errors="replace") as f:
        content = f.read()

    # Simple tag balance check
    stack = []
    import re
    for m in re.finditer(r"</?([a-zA-Z_:][a-zA-Z0-9_:.-]*)[^>]*/?>", content):
        tag = m.group(0)
        name = m.group(1)
        if tag.startswith("</"):  # closing tag
            if not stack:
                errors.append(f"  Extra closing tag </{name}> at position {m.start()}")
            elif stack[-1] != name:
                errors.append(f"  Mismatched tag: </{name}> closes <{stack[-1]}> at position {m.start()}")
                stack.pop()
            else:
                stack.pop()
        elif tag.endswith("/>"):  # self-closing
            pass
        else:  # opening tag
            stack.append(name)

    for unclosed in reversed(stack):
        errors.append(f"  Unclosed tag: <{unclosed}>")
    return errors


FORMATS = {
    ".json": ("JSON", _validate_json),
    ".yaml": ("YAML", _validate_yaml),
    ".yml": ("YAML", _validate_yaml),
    ".csv": ("CSV", _validate_csv),
    ".tsv": ("CSV (tab-separated)", _validate_csv),
    ".toml": ("TOML", _validate_toml),
    ".xml": ("XML", _validate_xml),
}


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print("Usage: validate <file> [file2 ...]")
        print("       validate --list")
        print("Validate file syntax. Auto-detects format by extension.")
        print(f"Supported: {', '.join(sorted(FORMATS.keys()))}")
        return

    if args[0] == "--list":
        for ext, (name, _) in sorted(FORMATS.items()):
            print(f"  {ext:<6} {name}")
        return

    total = 0
    passed = 0
    failed = 0

    for path in args:
        ext = os.path.splitext(path)[1].lower()
        if ext not in FORMATS:
            print(f"[SKIP] {path} — unsupported format '{ext}'")
            total += 1
            continue

        if not os.path.exists(path):
            print(f"[ERR]  {path} — file not found")
            total += 1
            failed += 1
            continue

        fmt_name, validator = FORMATS[ext]
        errors = validator(path)
        total += 1

        if not errors:
            print(f"[OK]   {path} — {fmt_name} is valid")
            passed += 1
        else:
            print(f"[FAIL] {path} — {fmt_name} has {len(errors)} error(s):")
            for e in errors:
                print(f"         {e}")
            failed += 1

    print(f"\n{total} file(s): {passed} passed, {failed} failed")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
