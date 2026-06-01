#!/usr/bin/env python3
"""markdown-to-html — Convert Markdown to simple HTML.

Usage: markdown-to-html input.md [output.html]
       cat README.md | markdown-to-html

Supports: headings, lists, code blocks, links, images, bold, italic, blockquotes.
Zero external dependencies.
"""

import sys
import re


def _escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _render_inline(text):
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    text = re.sub(r'\!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1">', text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    return text


def main():
    args = sys.argv[1:]
    if '-h' in args or '--help' in args:
        print(__doc__)
        return
    try:
        if args:
            with open(args[0]) as f:
                lines = f.readlines()
        else:
            lines = sys.stdin.readlines()
    except FileNotFoundError:
        print(f"Error: file not found", file=sys.stderr)
        sys.exit(1)
    html_parts = ['<!DOCTYPE html><html><head><meta charset="utf-8">'
                  '<title>Markdown</title></head><body>']
    in_code = False
    in_list = False
    in_blockquote = False
    code_content = []
    for line in lines:
        raw = line.rstrip("\n").rstrip("\r")
        # Code block
        if raw.startswith("```"):
            if in_code:
                html_parts.append("<pre><code>" + _escape("\n".join(code_content)) + "</code></pre>\n")
                code_content = []
                in_code = False
                continue
            else:
                if in_list:
                    html_parts.append("</ul>\n")
                    in_list = False
                if in_blockquote:
                    html_parts.append("</blockquote>\n")
                    in_blockquote = False
                in_code = True
                continue
        if in_code:
            code_content.append(raw)
            continue
        if in_list:
            if raw.startswith("- ") or raw.startswith("* "):
                html_parts.append(f"<li>{_render_inline(raw[2:])}</li>\n")
                continue
            else:
                html_parts.append("</ul>\n")
                in_list = False
        if not raw.strip():
            if in_blockquote:
                html_parts.append("</blockquote>\n")
                in_blockquote = False
            continue
        # Headings
        m = re.match(r'^(#{1,6})\s+(.+)$', raw)
        if m:
            level = len(m.group(1))
            html_parts.append(f"<h{level}>{_render_inline(m.group(2))}</h{level}>\n")
            continue
        # Blockquote
        if raw.startswith("> "):
            if not in_blockquote:
                html_parts.append("<blockquote>\n")
                in_blockquote = True
            html_parts.append(f"{_render_inline(raw[2:])}<br>\n")
            continue
        # List
        if raw.startswith("- ") or raw.startswith("* "):
            if not in_list:
                html_parts.append("<ul>\n")
                in_list = True
            html_parts.append(f"<li>{_render_inline(raw[2:])}</li>\n")
            continue
        # Horizontal rule
        if re.match(r'^-{3,}$', raw) or re.match(r'^\*{3,}$', raw):
            html_parts.append("<hr>\n")
            continue
        # Paragraph
        html_parts.append(f"<p>{_render_inline(raw)}</p>\n")
    if in_list:
        html_parts.append("</ul>\n")
    if in_blockquote:
        html_parts.append("</blockquote>\n")
    if in_code:
        html_parts.append("<pre><code>" + _escape("\n".join(code_content)) + "</code></pre>\n")
    html_parts.append("</body></html>\n")
    html_out = "".join(html_parts)
    if len(args) > 1:
        with open(args[1], 'w') as f:
            f.write(html_out)
    else:
        print(html_out)


TOOL_META = {
    "name": "markdown-to-html",
    "func": "main",
    "desc": "Convert Markdown to simple HTML (stdlib, zero deps)"
}
