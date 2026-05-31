#!/usr/bin/env python3
"""html-strip — Strip HTML tags, extract plain text from HTML."""
TOOL_META = {"name": "html-strip", "desc": "Strip HTML tags, extract plain text", "func": "main"}

import sys
import argparse
from html.parser import HTMLParser


class HTMLStripper(HTMLParser):
    """HTML parser that extracts plain text."""

    def __init__(self, preserve_links=False, minify=False):
        super().__init__(convert_charrefs=True)
        self.preserve_links = preserve_links
        self.minify = minify
        self._result = []
        self._links = []
        self._skip_text = False
        self._list_depth = 0

    def handle_starttag(self, tag, attrs):
        tag_lower = tag.lower()
        if tag_lower in ("script", "style"):
            self._skip_text = True
        elif tag_lower == "li":
            self._result.append("\n  " + "  " * self._list_depth + "• ")
            self._list_depth += 1
        elif tag_lower in ("p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "hr", "br", "blockquote"):
            self._result.append("\n")
        elif tag_lower in ("td", "th"):
            self._result.append("\t")
        elif tag_lower == "img":
            alt = ""
            src = ""
            for k, v in attrs:
                if k == "alt":
                    alt = v or ""
                elif k == "src":
                    src = v or ""
            if alt:
                self._result.append(alt)
            if self.preserve_links and src:
                self._links.append(src)
                self._result.append(f" [{src}]")
        if self.preserve_links:
            for k, v in attrs:
                if k == "href" and v and not v.startswith("#"):
                    self._links.append(v)

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower in ("script", "style"):
            self._skip_text = False
        elif tag_lower in ("p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "li", "blockquote"):
            self._result.append("\n")
        elif tag_lower == "li":
            self._list_depth = max(0, self._list_depth - 1)

    def handle_data(self, data):
        if not self._skip_text:
            self._result.append(data)

    def get_text(self):
        text = "".join(self._result)
        lines = text.split("\n")
        cleaned = []
        for line in lines:
            line = line.strip()
            if line:
                if self.minify:
                    import re
                    line = re.sub(r'\s+', ' ', line)
                cleaned.append(line)
            else:
                if cleaned and cleaned[-1] != "":
                    cleaned.append("")
        # Remove trailing empty lines
        while cleaned and cleaned[-1] == "":
            cleaned.pop()
        text = "\n".join(cleaned)

        if self.preserve_links and self._links:
            text += "\n\n--- Links ---\n"
            seen = set()
            for link in self._links:
                if link not in seen:
                    text += f"  {link}\n"
                    seen.add(link)
        return text


def strip_html(html_content, preserve_links=False, minify=False):
    """Strip HTML and return plain text."""
    stripper = HTMLStripper(preserve_links=preserve_links, minify=minify)
    stripper.feed(html_content)
    return stripper.get_text()


def main():
    parser = argparse.ArgumentParser(
        description="Strip HTML tags and extract plain text.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  html-strip --file index.html
  cat index.html | html-strip
  html-strip < index.html --preserve-links
  curl -s https://example.com | html-strip --minify
        """,
    )
    parser.add_argument("--file", "-f", help="HTML file to process")
    parser.add_argument("--preserve-links", "-l", action="store_true",
                        help="Show URLs from href/src in brackets")
    parser.add_argument("--minify", "-m", action="store_true",
                        help="Collapse whitespace, single-line output per paragraph")
    args = parser.parse_args()

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8", errors="replace") as f:
                html = f.read()
        except FileNotFoundError:
            print(f"Error: file not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        if sys.stdin.isatty():
            print("Reading HTML from stdin (Ctrl+D to end)...", file=sys.stderr)
        html = sys.stdin.read()

    if not html.strip():
        print("", file=sys.stderr)
        sys.exit(0)

    result = strip_html(html, preserve_links=args.preserve_links, minify=args.minify)
    print(result)


if __name__ == "__main__":
    main()
