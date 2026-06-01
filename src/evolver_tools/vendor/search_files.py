#!/usr/bin/env python3
"""search-files — Enhanced file search with regex support."""
import os
import re
import sys

TOOL_META = {
    "name": "search-files",
    "func": "main",
    "desc": "Search files by name/content. Usage: search-files <pattern> [path] [--type f|d]",
}

def search_by_name(pattern, root, file_type):
    results = []
    for root_dir, dirs, files in os.walk(root):
        if file_type in ("f", None):
            for f in files:
                try:
                    if re.search(pattern, f, re.IGNORECASE):
                        results.append(os.path.join(root_dir, f))
                except re.error:
                    if pattern.lower() in f.lower():
                        results.append(os.path.join(root_dir, f))
        if file_type in ("d", None):
            for d in dirs:
                try:
                    if re.search(pattern, d, re.IGNORECASE):
                        results.append(os.path.join(root_dir, d + "/"))
                except re.error:
                    if pattern.lower() in d.lower():
                        results.append(os.path.join(root_dir, d + "/"))
    return results

def search_by_content(pattern, root, file_glob=None):
    results = []
    for root_dir, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "__pycache__", ".git")]
        for f in files:
            if file_glob and not f.endswith(file_glob):
                continue
            fp = os.path.join(root_dir, f)
            try:
                with open(fp, "r", errors="ignore") as fh:
                    for i, line in enumerate(fh, 1):
                        if re.search(pattern, line, re.IGNORECASE):
                            results.append((fp, i, line.rstrip()[:120]))
            except Exception:
                pass
    return results

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: search-files <pattern> [path] [--type f|d] [--content] [--glob *.py]")
        sys.exit(1)
    pattern = args[0]
    path = "."
    file_type = None
    search_content = False
    file_glob = None
    i = 1
    while i < len(args):
        if args[i] == "--type" and i + 1 < len(args):
            file_type = args[i + 1]
            i += 2
        elif args[i] == "--content":
            search_content = True
            i += 1
        elif args[i] == "--glob" and i + 1 < len(args):
            file_glob = args[i + 1]
            i += 2
        elif not args[i].startswith("-"):
            path = args[i]
            i += 1
        else:
            i += 1
    path = os.path.abspath(path)
    if search_content:
        results = search_by_content(pattern, path, file_glob)
        if results:
            print(f"Found {len(results)} matches:")
            for fp, line_num, text in results[:50]:
                rel = os.path.relpath(fp, os.getcwd())
                print(f"  {rel}:{line_num}: {text}")
            if len(results) > 50:
                print(f"  ... and {len(results) - 50} more")
        else:
            print("No matches found")
    else:
        results = search_by_name(pattern, path, file_type)
        if results:
            print(f"Found {len(results)} matches:")
            for r in results[:50]:
                print(f"  {os.path.relpath(r, os.getcwd())}")
            if len(results) > 50:
                print(f"  ... and {len(results) - 50} more")
        else:
            print("No files found matching pattern")

if __name__ == "__main__":
    main()
