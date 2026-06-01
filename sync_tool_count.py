#!/usr/bin/env python3
"""Sync tool count from actual source into all docs, marketing, and HTML files.

Run from evolver-tools project root. Auto-detects actual tool count from TOOL_META.
"""
import os
import re
import sys
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(PROJECT_ROOT, "src", "evolver_tools")


def get_actual_tool_count():
    """Count actual tool files and TOOL_META entries."""
    r = subprocess.run(
        ["grep", "-rl", "TOOL_META", "--include=*.py", "."],
        capture_output=True, text=True, cwd=SRC_DIR,
    )
    files = [f for f in r.stdout.strip().split("\n") if f]
    
    r2 = subprocess.run(
        ["grep", "-r", "TOOL_META", "--include=*.py", "."],
        capture_output=True, text=True, cwd=SRC_DIR,
    )
    entries = [l for l in r2.stdout.strip().split("\n") if l and "TOOL_META" in l]
    
    return len(files), len(entries)


def get_version():
    """Get version from __init__.py."""
    init_path = os.path.join(SRC_DIR, "__init__.py")
    with open(init_path) as f:
        m = re.search(r'__version__\s*=\s*"([^"]+)"', f.read())
    return m.group(1) if m else "0.0.0"


def update_file(path, old, new):
    """Replace old string with new in file. Returns True if changed."""
    if not os.path.exists(path):
        return False
    with open(path) as f:
        content = f.read()
    if old not in content:
        return False
    content = content.replace(old, new)
    with open(path, "w") as f:
        f.write(content)
    return True


def update_file_patterns(path, replacements, version_replacements):
    """Apply multiple replacements. Returns count of changes."""
    if not os.path.exists(path):
        return 0
    with open(path) as f:
        content = f.read()
    changed = 0
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            changed += 1
    for old, new in version_replacements:
        if old in content:
            content = content.replace(old, new)
            changed += 1
    if changed:
        with open(path, "w") as f:
            f.write(content)
        print(f"  ✏️  {path} ({changed} changes)")
    return changed


def main():
    dry = "--dry-run" in sys.argv
    
    tool_files, tool_entries = get_actual_tool_count()
    tool_str = str(tool_entries)
    version = get_version()
    
    print(f"📊 Actual: {tool_files} files, {tool_entries} tools (TOOL_META entries)")
    print(f"📦 Version: {version}")
    print(f"{'🔍 DRY RUN' if dry else '⚡ UPDATING'} — {'no files will be written' if dry else 'files will be modified'}")
    print()
    
    total_changes = 0
    
    # Define old values to replace
    old_counts = ["260", "262", "259", "258", "254", "252"]
    old_versions = [
        "v38.0.18", "v38.0.17", "v38.0.16", "v38.0.15",
        "38.0.18", "38.0.17", "38.0.16", "38.0.15",
    ]
    
    # Build replacements: "260 tools" -> "260 tools", "260+" -> "276+", etc.
    count_replacements = []
    for oc in old_counts:
        count_replacements.extend([
            (f"{oc} tools", f"{tool_str} tools"),
            (f'{oc}" tool', f'{tool_str}" tool'),  # JSON
            (f"{oc}+ tools", f"{tool_str}+ tools"),
            (f"{oc} CLI tools", f"{tool_str} CLI tools"),
            (f"{oc} CLI Tools", f"{tool_str} CLI Tools"),
            (f"> {oc}</", f"> {tool_str}</"),
            (f":{oc}</", f":{tool_str}</"),
            (f"num\">{oc}<", f"num\">{tool_str}<"),
            (f'"tools":{oc}', f'"tools":{tool_str}'),
            (f"cowsay '{oc}", f"cowsay '{tool_str}"),  # gallery scripts
            (f"tools\\\\\":{oc}", f"tools\\\\\":{tool_str}"),  # escaped JSON in JS
            (f"tools\":{oc}", f"tools\":{tool_str}"),  # unescaped JSON in JS
            (f"All {oc} tools", f"All {tool_str} tools"),
            (f"all {oc} tools", f"all {tool_str} tools"),
            (f"all {oc} CLI", f"all {tool_str} CLI"),
            (f"of {oc} tools", f"of {tool_str} tools"),
            (f"({oc} total)", f"({tool_str} total)"),
            # stat div patterns
            (f">{oc}<", f">{tool_str}<"),
        ])
    
    version_replacements = []
    for ov in old_versions:
        v = version if ov.startswith("v") else version  # preserve v prefix
        version_replacements.append((ov, version if not ov.startswith("v") else f"v{version}"))
    
    # Walk files
    for root, dirs, files in os.walk(PROJECT_ROOT):
        # Skip source and hidden dirs
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("src", "__pycache__", "node_modules", ".git")]
        
        for fname in files:
            if not fname.endswith((".html", ".md", ".sh", ".json", ".yml", ".yaml", ".toml")):
                continue
            fpath = os.path.join(root, fname)
            # Skip binary files
            try:
                with open(fpath) as f:
                    f.read(100)
            except:
                continue
            
            # Smart: only update if file contains old patterns
            with open(fpath) as f:
                content = f.read()
            
            needs_update = False
            for oc in old_counts:
                if oc in content:
                    needs_update = True
                    break
            if not needs_update:
                for ov in old_versions:
                    if ov in content:
                        needs_update = True
                        break
            if not needs_update:
                continue
            
            # Only apply exact patterns to avoid over-matching
            changes = 0
            for old, new in count_replacements:
                # Check if this pattern actually occurs in the file
                if old in content:
                    content = content.replace(old, new)
                    changes += 1
            
            for old, new in version_replacements:
                if old in content:
                    content = content.replace(old, new)
                    changes += 1
            
            if changes:
                if not dry:
                    with open(fpath, "w") as f:
                        f.write(content)
                print(f"  {'📝' if dry else '✏️'}  {os.path.relpath(fpath, PROJECT_ROOT)} ({changes} changes)")
                total_changes += changes
    
    print()
    if total_changes:
        print(f"✅ {total_changes} replacements across files.")
    else:
        print("✅ All files already up to date.")
    
    # Summary
    print()
    print(f"📋 Summary:")
    print(f"   Tools: {tool_str} (was 260)")
    print(f"   Version: {version} (was 38.0.18 on live site)")
    print(f"   Next: push to GitHub when connection is available")


if __name__ == "__main__":
    main()
