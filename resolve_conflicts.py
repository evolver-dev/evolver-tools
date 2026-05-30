#!/usr/bin/env python3
"""Resolve git conflicts and patch missing TOOL_META."""

import os
import re
import sys

REPO = "/root/evolver-tools"
VENDOR_DIR = os.path.join(REPO, "src/evolver_tools/vendor")

# --- Step 1: Resolve pyproject.toml ---
# Take our version (v3.0.0) but with remote's additional metadata
pyproj_path = os.path.join(REPO, "pyproject.toml")
with open(pyproj_path) as f:
    content = f.read()

# Remove conflict markers
content = re.sub(r'<<<<<<< HEAD\n.*?\n=======\n', '', content, flags=re.DOTALL)
content = re.sub(r'\n>>>>>>> [^\n]+\n', '\n', content)
content = re.sub(r'>>>>>>> [^\n]+\n', '\n', content)

# Ensure version is 3.0.0
content = re.sub(r'version = "\d+\.\d+\.\d+"', 'version = "3.0.0"', content)
content = re.sub(r'description = ".*?"', 'description = "99 essential CLI tools - one pip install"', content)

with open(pyproj_path, 'w') as f:
    f.write(content)
print("Resolved pyproject.toml (v3.0.0, 99 tools)")

# --- Step 2: autoreg.py - use ours ---
# Remove conflict markers from autoreg.py
autoreg_path = os.path.join(REPO, "src/evolver_tools/autoreg.py")
if os.path.exists(autoreg_path):
    with open(autoreg_path) as f:
        content = f.read()
    content = re.sub(r'<<<<<<< HEAD\n.*?\n=======\n', '', content, flags=re.DOTALL)
    content = re.sub(r'\n>>>>>>> [^\n]+\n', '\n', content)
    with open(autoreg_path, 'w') as f:
        f.write(content)
    print("Resolved autoreg.py")

# --- Step 3: cli.py - use ours ---
cli_path = os.path.join(REPO, "src/evolver_tools/cli.py")
with open(cli_path) as f:
    content = f.read()
content = re.sub(r'<<<<<<< HEAD\n.*?\n=======\n', '', content, flags=re.DOTALL)
content = re.sub(r'\n>>>>>>> [^\n]+\n', '\n', content)
with open(cli_path, 'w') as f:
    f.write(content)
print("Resolved cli.py")

# --- Step 4: cal_tool/__init__.py ---
cal_init = os.path.join(VENDOR_DIR, "cal_tool/__init__.py")
with open(cal_init) as f:
    content = f.read()
content = re.sub(r'<<<<<<< HEAD\n.*?\n=======\n', '', content, flags=re.DOTALL)
content = re.sub(r'\n>>>>>>> [^\n]+\n', '\n', content)
with open(cal_init, 'w') as f:
    f.write(content)
print("Resolved cal_tool/__init__.py")

# --- Step 5: Find tools WITHOUT TOOL_META ---
print("\n=== Tools missing TOOL_META ===")
tools_dir = VENDOR_DIR
all_files = []

for entry in os.listdir(tools_dir):
    entry_path = os.path.join(tools_dir, entry)
    if entry.endswith(".py") and entry != "__init__.py":
        all_files.append(("file", entry, entry_path))
    elif os.path.isdir(entry_path) and not entry.startswith("__"):
        init = os.path.join(entry_path, "__init__.py")
        if os.path.exists(init):
            all_files.append(("pkg", entry, init))

missing = []
for ftype, fname, fpath in all_files:
    with open(fpath) as f:
        content = f.read()
    if "TOOL_META" not in content:
        missing.append((ftype, fname, fpath))
        print(f"  MISSING TOOL_META: {ftype} {fname} ({fpath})")

if missing:
    print(f"\n{len(missing)} files need TOOL_META")
else:
    print("  All tools have TOOL_META!")

# --- Step 6: Mark conflicts as resolved ---
os.system(f"cd {REPO} && git add pyproject.toml src/evolver_tools/autoreg.py src/evolver_tools/cli.py src/evolver_tools/vendor/cal_tool/__init__.py")

print("\nRun 'git rebase --continue' next")
