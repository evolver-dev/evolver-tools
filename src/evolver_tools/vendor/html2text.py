#!/usr/bin/env python3
"""html2text.py — Convert HTML to plain text.

Pure Python using html.parser from stdlib. No external dependencies.
Reads from --file FILE or stdin. Outputs clean plain text with:
  - Stripped tags, preserved paragraph breaks
  - Headings rendered with === / --- underlines
  - Links shown as [text](url)
  - Lists with * bullets
  - Scripts and styles stripped
"""

from html.parser import HTMLParser
import argparse
import sys
import re


TOOL_META = {
    "name": "html2text",
    "func": "main",
    "desc": "Convert HTML to plain text",
}


class _HTML2Text(HTMLParser):
    """HTML parser that accumulates plain text output."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out_lines = []          # final lines of output
        self._buf = ""               # current line buffer
        self._pre = False
        self._skip = 0               # nesting depth inside <script>/<style>
        self._list_depth = 0
        self._heading_level = 0

        # Link handling: buffer anchor text, emit [text](url) on </a>
        self._anchor_href = None
        self._anchor_buf = ""

        # Track blank lines to avoid multiples
        self._last_was_newline = False

    # -- helpers -----------------------------------------------------------

    def _flush(self):
        """Push current buffer as a line."""
        s = self._buf.strip()
        if s:
            self.out_lines.append(s)
            self._last_was_newline = False
        self._buf = ""

    def _newline(self):
        """Add a blank line separator."""
        self._flush()
        if not self._last_was_newline:
            self.out_lines.append("")
            self._last_was_newline = True

    def _emit(self, text):
        self._buf += text

    # -- parser callbacks --------------------------------------------------

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in ("script", "style"):
            self._skip += 1
            return

        if self._skip:
            return

        attrs_dict = dict(attrs)

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._newline()
            self._heading_level = int(tag[1])

        elif tag in ("p", "div", "section", "article", "blockquote",
                     "figure", "figcaption", "header", "footer", "nav",
                     "main", "aside", "address", "details", "summary"):
            self._newline()

        elif tag in ("br", "hr"):
            self._flush()

        elif tag in ("ul", "ol"):
            self._newline()
            self._list_depth += 1

        elif tag == "li":
            self._flush()
            indent = "  " * (self._list_depth - 1) if self._list_depth > 1 else ""
            self._emit(indent + "* ")

        elif tag == "a":
            href = attrs_dict.get("href", "").strip()
            self._anchor_href = href if href else None
            self._anchor_buf = ""

        elif tag in ("b", "strong", "em", "i", "u", "mark", "code",
                     "kbd", "samp", "pre", "span"):
            pass  # inline — just append content

        elif tag == "img":
            alt = attrs_dict.get("alt", "")
            if alt:
                self._emit(alt)

        elif tag in ("table", "tr", "td", "th", "thead", "tbody", "tfoot"):
            pass

        elif tag == "pre":
            self._pre = True
            self._newline()

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in ("script", "style"):
            if self._skip > 0:
                self._skip -= 1
            return

        if self._skip:
            return

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._flush()
            text = self.out_lines[-1] if self.out_lines else ""
            if self._heading_level <= 2:
                self.out_lines.append("=" * max(len(text), 1))
            else:
                self.out_lines.append("-" * max(len(text), 1))
            self._last_was_newline = False
            self._newline()

        elif tag in ("p", "div", "section", "article", "blockquote",
                     "figure", "figcaption", "header", "footer", "nav",
                     "main", "aside", "address"):
            self._newline()

        elif tag == "pre":
            self._pre = False
            self._flush()
            self._newline()

        elif tag in ("ul", "ol"):
            self._list_depth = max(0, self._list_depth - 1)
            self._flush()
            self._newline()

        elif tag == "li":
            pass  # line already flushed on <li>

        elif tag == "a":
            href = self._anchor_href
            text = self._anchor_buf.strip()
            self._anchor_href = None
            self._anchor_buf = ""
            if href is not None and text:
                self._emit("[{}]({})".format(text, href))
            elif text:
                self._emit(text)
            # if href without text, emit nothing

        elif tag == "br":
            self._flush()

    def handle_data(self, data):
        if self._skip:
            return
        if self._pre:
            self._emit(data)
        else:
            cleaned = re.sub(r"\s+", " ", data)
            if cleaned:
                if self._anchor_href is not None:
                    self._anchor_buf += cleaned
                else:
                    self._emit(cleaned)

    def get_text(self):
        """Finalize and return the plain text result."""
        if self._buf.strip():
            self._flush()
        # Remove trailing blank lines
        while self.out_lines and self.out_lines[-1] == "":
            self.out_lines.pop()
        # Add single trailing newline
        return "\n".join(self.out_lines) + "\n"


def html2text(html: str) -> str:
    """Convert an HTML string to plain text."""
    parser = _HTML2Text()
    parser.feed(html)
    parser.close()
    return parser.get_text()


def main(argv=None) -> int:
    """CLI entry point for html2text."""
    parser = argparse.ArgumentParser(
        description="Convert HTML to plain text.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python html2text.py --file input.html\n"
            "  cat input.html | python html2text.py\n"
            "  curl -s https://example.com | python html2text.py\n"
        ),
    )
    parser.add_argument(
        "--file", "-f",
        type=str,
        default=None,
        metavar="FILE",
        help="Input HTML file (omit to read from stdin).",
    )
    args = parser.parse_args(argv)

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as fh:
                html_content = fh.read()
        except FileNotFoundError:
            print("Error: file not found -- {}".format(args.file), file=sys.stderr)
            return 1
        except IOError as exc:
            print("Error: cannot read {} -- {}".format(args.file, exc), file=sys.stderr)
            return 1
    else:
        html_content = sys.stdin.read()

    result = html2text(html_content)
    sys.stdout.write(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
