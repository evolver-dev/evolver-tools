#!/usr/bin/env python3
"""Sync tool count from the actual registry into all docs and marketing files.

Run from the evolver-tools project root."""
import sys
import os
import re

# Actual tool count
TOOL_COUNT = "259"

# Files to fix with their old/new patterns
FIXES = {
    # --- try.sh ---
    "try.sh": [
        ("254 CLI tools · zero deps · one pip install", "259 CLI tools · zero deps · one pip install"),
        ('"name":"evolver","tools":254', '"name":"evolver","tools":259'),
        ("254 tools ready", "259 tools ready"),
        ("Browse all 254 tools", "Browse all 259 tools"),
    ],
    # --- README.md (remaining inconsistencies) ---
    "README.md": [
        ("See all 254 tools:", "See all 259 tools:"),
        ("All 254 tools, full source, forever", "All 259 tools, full source, forever"),
        ("Data drift in tool count (252 → 254)", "Data drift in tool count (252 → 259)"),
        ("v37.0.0 — 2026-06-01 (+5 tools, 254 total)", "v37.0.0 — 2026-06-01 (+5 tools, 259 total)"),
        ("v36.0.0 — 2026-06-01 (+5 tools, 254 total)", "v36.0.0 — 2026-06-01 (+5 tools, 259 total)"),
        ("254 zero-dependency CLI tools are built", "259 zero-dependency CLI tools are built"),
    ],
}

# --- CLAUDE.md ---
CLAUDE_FIXES = {
    "CLAUDE.md": [
        ("**254 zero-dependency CLI tools**", "**259 zero-dependency CLI tools**"),
        ("Quick Reference section says 254", "Quick Reference section"),
        ("Total: 254 tools", "Total: 259 tools"),
    ],
}

HTML_PATTERNS = {
    "254": "259",
    "254 essential": "259 essential",
    "254 CLI Tools": "259 CLI Tools",
    "254 CLI tools": "259 CLI tools",
    "254 tools": "259 tools",
    "v38.0.0 · 254": "v38.0.0 · 259",
    "num\">254<": "num\">259<",
    "All 254 tools": "All 259 tools",
    "254 tools isn": "259 tools isn",
    "254 tools · 0": "259 tools · 0",
}

def fix_file(path, replacements, dry_run=False):
    if not os.path.exists(path):
        print(f"  SKIP (not found): {path}")
        return 0
    
    with open(path) as f:
        content = f.read()
    
    count = 0
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            count += 1
            print(f"  FIX: {path} → '{old[:50]}...'")
    
    if not dry_run and count > 0:
        with open(path, 'w') as f:
            f.write(content)
        print(f"  → Wrote {path}")
    
    return count

def fix_html_file(path, dry_run=False):
    """Fix HTML files using regex patterns for the tool count."""
    if not os.path.exists(path):
        print(f"  SKIP (not found): {path}")
        return 0
    
    with open(path) as f:
        content = f.read()
    
    original = content
    for old_pattern, new_text in HTML_PATTERNS.items():
        content = content.replace(old_pattern, new_text)
    
    changes = content != original
    if changes:
        print(f"  FIX: {path} (tool count updated)")
        if not dry_run:
            with open(path, 'w') as f:
                f.write(content)
    
    return 1 if changes else 0


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    root = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "."
    
    print(f"{'DRY RUN' if dry else 'UPDATE'} — Tool count: {TOOL_COUNT}")
    print(f"Root: {root}")
    print()
    
    total = 0
    
    # Fix core files
    for file, fixes in FIXES.items():
        total += fix_file(os.path.join(root, file), fixes, dry)
    
    # Fix CLAUDE.md
    for file, fixes in CLAUDE_FIXES.items():
        total += fix_file(os.path.join(root, file), fixes, dry)
    
    # Fix HTML docs
    docs_dir = os.path.join(root, "docs")
    if os.path.isdir(docs_dir):
        for fname in sorted(os.listdir(docs_dir)):
            if fname.endswith(".html"):
                total += fix_html_file(os.path.join(docs_dir, fname), dry)
    
    # Fix marketing files
    mkt_dir = os.path.join(root, "marketing")
    if os.path.isdir(mkt_dir):
        for fname in sorted(os.listdir(mkt_dir)):
            fpath = os.path.join(mkt_dir, fname)
            if fname.endswith(".md"):
                total += fix_file(fpath, [
                    ("254", "259"),
                ], dry)
    
    print(f"\n{'→' if dry else '✓'} {total} files updated.")
