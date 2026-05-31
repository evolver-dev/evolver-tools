#!/usr/bin/env python3
"""link-check — Check for broken links in Markdown files.

Usage: link-check README.md
       link-check docs/ --recursive
       link-check README.md --timeout 5
       link-check README.md --skip-local
       link-check README.md --verbose
"""

import os
import re
import sys
import urllib.error
import urllib.request
import pathlib


def find_markdown_files(paths, recursive):
    """Collect markdown files from given paths."""
    files = []
    for p in paths:
        p = pathlib.Path(p)
        if p.is_file() and p.suffix.lower() in ('.md', '.markdown'):
            files.append(p)
        elif p.is_dir():
            if recursive:
                for f in sorted(p.rglob('*')):
                    if f.is_file() and f.suffix.lower() in ('.md', '.markdown'):
                        files.append(f)
            else:
                for f in sorted(p.glob('*.md')):
                    files.append(f)
                for f in sorted(p.glob('*.markdown')):
                    files.append(f)
        else:
            print(f"  Warning: not a file or directory: {p}", file=sys.stderr)
    return files


def extract_links(content, base_dir):
    """Extract all URLs from markdown content.

    Handles [text](url) and <url> patterns. Returns list of (url, line_number).
    """
    links = []
    for i, line in enumerate(content.splitlines(), 1):
        # [text](url) pattern
        for m in re.finditer(r'\[([^\]]*)\]\(([^)]+)\)', line):
            url = m.group(2).strip()
            # Skip empty URLs and anchors-only
            if url and not url.startswith('#'):
                links.append((url, i))
        # <url> pattern (autolink)
        for m in re.finditer(r'(?<![\(\[])https?://[^\s<>\)\]]+', line):
            url = m.group(0).strip().rstrip('.,;:!?)')
            if url:
                links.append((url, i))
    return links


def check_http_link(url, timeout, verbose):
    """Check an HTTP/HTTPS link using HEAD request, fallback to GET."""
    try:
        req = urllib.request.Request(url, method='HEAD')
        # Set a User-Agent to avoid blocks
        req.add_header('User-Agent', 'link-check/1.0')
        resp = urllib.request.urlopen(req, timeout=timeout)
        status = resp.status
        resp.close()
        ok = 200 <= status < 400
        if verbose:
            return ok, f"HTTP {status}"
        return ok, None
    except (urllib.error.HTTPError, urllib.error.URLError,
            OSError, ValueError) as e:
        # Some servers reject HEAD, try GET with range
        try:
            req = urllib.request.Request(url, method='GET')
            req.add_header('User-Agent', 'link-check/1.0')
            req.add_header('Range', 'bytes=0-0')
            resp = urllib.request.urlopen(req, timeout=timeout)
            status = resp.status
            resp.close()
            ok = 200 <= status < 400
            if verbose:
                return ok, f"HTTP {status}"
            return ok, None
        except Exception:
            reason = str(e).split(':')[0].strip()
            if verbose:
                return False, reason
            return False, None


def main():
    args = sys.argv[1:]

    if '-h' in args or '--help' in args or not args:
        print(__doc__)
        sys.exit(0)

    # Parse options
    recursive = False
    skip_local = False
    skip_external = False
    verbose = False
    quiet = False
    timeout = 5

    positional = []
    i = 0
    while i < len(args):
        a = args[i]
        if a in ('-r', '--recursive'):
            recursive = True
        elif a in ('-t', '--timeout'):
            i += 1
            if i < len(args):
                timeout = int(args[i])
        elif a == '--skip-local':
            skip_local = True
        elif a == '--skip-external':
            skip_external = True
        elif a in ('-v', '--verbose'):
            verbose = True
        elif a in ('-q', '--quiet'):
            quiet = True
        else:
            positional.append(a)
        i += 1

    if not positional:
        print(__doc__)
        sys.exit(2)

    files = find_markdown_files(positional, recursive)
    if not files:
        print("  No markdown files found.", file=sys.stderr)
        sys.exit(2)

    total_links = 0
    broken_links = 0
    exit_code = 0

    for filepath in files:
        try:
            content = filepath.read_text(encoding='utf-8')
        except Exception as e:
            if not quiet:
                print(f"  Error reading {filepath}: {e}", file=sys.stderr)
            continue

        links = extract_links(content, filepath.parent)
        if not links:
            continue

        base_dir = filepath.parent
        for url, lineno in links:
            total_links += 1
            display_url = url if len(url) <= 70 else url[:67] + '...'

            # Skip mailto: links
            if url.startswith('mailto:'):
                continue

            if url.startswith(('http://', 'https://')):
                if skip_external:
                    continue
                ok, extra = check_http_link(url, timeout, verbose)
            elif url.startswith('file://'):
                if skip_local:
                    continue
                local_path = url.replace('file://', '', 1)
                if os.name == 'nt':
                    local_path = local_path.lstrip('/')
                ok = os.path.exists(local_path)
                extra = None
            else:
                # Relative or absolute local path
                if skip_local:
                    continue
                target = (base_dir / url).resolve()
                ok = target.exists()
                extra = None

            if ok:
                if not quiet:
                    status = f"  ✓ {display_url}"
                    if verbose and extra:
                        status += f" ({extra})"
                    print(status)
            else:
                broken_links += 1
                exit_code = 1
                status = f"  ✗ {display_url}"
                if verbose and extra:
                    status += f" ({extra})"
                print(status)

    if total_links == 0:
        if not quiet:
            print("  No links found.")
    else:
        summary = (
            f"\n  Checked {total_links} link{'s' if total_links != 1 else ''}: "
            f"{broken_links} broken"
        )
        if not quiet:
            print(summary)

    sys.exit(exit_code)


TOOL_META = {
    "name": "link-check",
    "func": "main",
    "desc": "Check for broken links in Markdown files"
}
