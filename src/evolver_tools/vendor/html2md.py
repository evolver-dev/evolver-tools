#!/usr/bin/env python3
"""html2md — Convert HTML to Markdown using stdlib HTMLParser."""
import sys
import os
import argparse
from html.parser import HTMLParser
import re


class HTMLToMarkdown(HTMLParser):
    """Convert HTML to Markdown."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.output = []
        self.in_pre = False
        self.in_code = False
        self.in_blockquote = False
        self.in_li = False
        self.in_table = False
        self.in_thead = False
        self.in_tbody = False
        self.in_tr = False
        self.in_th = False
        self.in_td = False
        self.skip_next_p = False
        self.list_stack = []  # (type, counter) where type is 'ul' or 'ol'
        self.header_level = 0
        self.table_rows = []
        self.current_row = []
        self.current_cell = ""
        self.is_header_row = False
        self.link_href = ""
        self.link_text = ""
        self.image_alt = ""
        self.image_src = ""
        self.bold_active = False
        self.italic_active = False
        self.code_text = ""
        self.pre_text = ""
        self.seen_text_since_block = False
        self.br_count = 0

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        tag = tag.lower()

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.header_level = int(tag[1])
            self.maybe_newline()
        elif tag == "p":
            if not self.skip_next_p:
                self.maybe_newline()
        elif tag == "br":
            self.output.append("  \n")
        elif tag == "hr":
            self.maybe_newline()
            self.output.append("\n---\n")
        elif tag == "strong" or tag == "b":
            self.bold_active = True
        elif tag == "em" or tag == "i":
            self.italic_active = True
        elif tag == "a":
            self.link_href = attrs_dict.get("href", "")
            self.link_text = ""
        elif tag == "img":
            alt = attrs_dict.get("alt", "")
            src = attrs_dict.get("src", "")
            title = attrs_dict.get("title", "")
            title_part = f' "{title}"' if title else ""
            self.output.append(f"![{alt}]({src}{title_part})")
        elif tag == "ul":
            self.list_stack.append(("ul", 0))
            self.maybe_newline()
            self.output.append("\n")
        elif tag == "ol":
            self.list_stack.append(("ol", 1))
            self.maybe_newline()
            self.output.append("\n")
        elif tag == "li":
            self.maybe_newline()
            self.in_li = True
        elif tag == "blockquote":
            self.in_blockquote = True
            self.maybe_newline()
            self.output.append("\n")
        elif tag == "pre":
            self.in_pre = True
            self.pre_text = ""
            self.maybe_newline()
            self.output.append("\n")
        elif tag == "code":
            if not self.in_pre:
                self.in_code = True
        elif tag == "table":
            self.in_table = True
            self.table_rows = []
            self.maybe_newline()
            self.output.append("\n")
        elif tag == "thead":
            self.in_thead = True
            self.is_header_row = True
        elif tag == "tbody":
            self.in_tbody = True
        elif tag == "tr":
            self.in_tr = True
            self.current_row = []
        elif tag == "th":
            self.in_th = True
            self.current_cell = ""
        elif tag == "td":
            self.in_td = True
            self.current_cell = ""

    def handle_endtag(self, tag):
        tag = tag.lower()

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.output.append("\n\n")
            self.header_level = 0
        elif tag == "p":
            if not self.skip_next_p:
                self.output.append("\n\n")
                self.seen_text_since_block = True
            self.skip_next_p = False
        elif tag == "strong" or tag == "b":
            self.bold_active = False
        elif tag == "em" or tag == "i":
            self.italic_active = False
        elif tag == "a":
            if self.link_text and self.link_href:
                self.output.append(f"[{self.link_text}]({self.link_href})")
            elif self.link_href:
                self.output.append(f"<{self.link_href}>")
            self.link_href = ""
            self.link_text = ""
        elif tag == "ul":
            if self.list_stack and self.list_stack[-1][0] == "ul":
                self.list_stack.pop()
                self.output.append("\n")
        elif tag == "ol":
            if self.list_stack and self.list_stack[-1][0] == "ol":
                self.list_stack.pop()
                self.output.append("\n")
        elif tag == "li":
            self.in_li = False
            self.output.append("\n")
        elif tag == "blockquote":
            self.in_blockquote = False
            self.output.append("\n")
        elif tag == "pre":
            self.in_pre = False
            self.output.append(self.pre_text)
            self.output.append("\n")
            self.pre_text = ""
        elif tag == "code":
            if self.in_code:
                self.in_code = False
        elif tag == "table":
            self.in_table = False
            self.render_table()
        elif tag == "thead":
            self.in_thead = False
        elif tag == "tbody":
            self.in_tbody = False
        elif tag == "tr":
            self.in_tr = False
            self.table_rows.append(list(self.current_row))
            self.current_row = []
        elif tag == "th":
            self.in_th = False
            self.current_row.append(self.current_cell.strip())
            self.current_cell = ""
        elif tag == "td":
            self.in_td = False
            self.current_row.append(self.current_cell.strip())
            self.current_cell = ""

    def handle_data(self, data):
        if self.in_pre:
            self.pre_text += data
            return

        if self.in_th or self.in_td:
            self.current_cell += data
            return

        if self.in_code:
            self.output.append(f"`{data}`")
            return

        text = data

        if self.in_li:
            if not self.list_stack:
                self.output.append(f"- {text}")
            elif self.list_stack[-1][0] == "ul":
                indent = "  " * (len(self.list_stack) - 1)
                self.output.append(f"{indent}- {text}")
            elif self.list_stack[-1][0] == "ol":
                indent = "  " * (len(self.list_stack) - 1)
                num = self.list_stack[-1][1]
                self.list_stack[-1] = ("ol", num + 1)
                self.output.append(f"{indent}{num}. {text}")
            return

        if self.in_blockquote:
            for line in text.split("\n"):
                if line.strip():
                    self.output.append(f"> {line}\n")
                else:
                    self.output.append(">\n")
            return

        if self.link_href:
            self.link_text += text
            return

        if self.header_level > 0:
            prefix = "#" * self.header_level
            text = f"{prefix} {text.strip()}"
            self.output.append(text)
            return

        if self.bold_active and self.italic_active:
            self.output.append(f"***{text}***")
        elif self.bold_active:
            self.output.append(f"**{text}**")
        elif self.italic_active:
            self.output.append(f"*{text}*")
        else:
            self.output.append(text)

    def handle_entityref(self, name):
        # Entity refs are converted by HTMLParser when convert_charrefs=True
        pass

    def render_table(self):
        """Render accumulated table data as markdown."""
        if not self.table_rows:
            return

        # Get max columns
        max_cols = max(len(row) for row in self.table_rows) if self.table_rows else 0
        if max_cols == 0:
            return

        # Find the header row (first row if we had thead, otherwise first row)
        if self.is_header_row and self.table_rows:
            header = self.table_rows[0][:max_cols]
            data_rows = self.table_rows[1:] if len(self.table_rows) > 1 else []
        else:
            header = self.table_rows[0][:max_cols] if self.table_rows else []
            data_rows = self.table_rows[1:] if len(self.table_rows) > 1 else []

        col_widths = []
        for i in range(max_cols):
            max_w = len(header[i]) if i < len(header) else 3
            for row in data_rows:
                val = row[i] if i < len(row) else ""
                max_w = max(max_w, len(val))
            col_widths.append(max(max_w, 3))

        # Render header
        header_cells = []
        for i in range(max_cols):
            val = header[i] if i < len(header) else ""
            header_cells.append(val.ljust(col_widths[i]))
        self.output.append("| " + " | ".join(header_cells) + " |\n")

        # Render separator
        sep_cells = []
        for w in col_widths:
            sep_cells.append("-" * w)
        self.output.append("| " + " | ".join(sep_cells) + " |\n")

        # Render data rows
        for row in data_rows:
            cells = []
            for i in range(max_cols):
                val = row[i] if i < len(row) else ""
                cells.append(val.ljust(col_widths[i]))
            self.output.append("| " + " | ".join(cells) + " |\n")

        self.output.append("\n")
        self.is_header_row = False

    def maybe_newline(self):
        """Add a newline if we have content."""
        if self.output and self.output[-1] != "\n\n":
            if self.output[-1].endswith("\n") and not self.output[-1].endswith("\n\n"):
                self.output.append("\n")

    def get_markdown(self):
        """Join output and cleanup extra whitespace."""
        result = "".join(self.output)
        # Collapse 3+ newlines to 2
        result = re.sub(r"\n{3,}", "\n\n", result)
        # Clean trailing whitespace per line
        lines = result.split("\n")
        lines = [line.rstrip() for line in lines]
        return "\n".join(lines).strip() + "\n"


def convert_file(filepath):
    """Convert an HTML file to markdown."""
    try:
        with open(filepath, "r") as f:
            html_content = f.read()
    except IOError as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
        sys.exit(1)
    return convert_string(html_content)


def convert_string(html_content):
    """Convert HTML string to markdown."""
    parser = HTMLToMarkdown()
    try:
        parser.feed(html_content)
        parser.close()
    except Exception as e:
        print(f"Error parsing HTML: {e}", file=sys.stderr)
        sys.exit(1)
    return parser.get_markdown()


def main():
    parser = argparse.ArgumentParser(
        description="Convert HTML to Markdown using stdlib HTMLParser."
    )
    parser.add_argument("file", nargs="?", help="HTML file to convert (default: stdin)")
    parser.add_argument("--clipboard", action="store_true", help="Read from clipboard (Linux: xclip)")

    args = parser.parse_args()

    if args.clipboard:
        # Read from clipboard via xclip or xsel
        import subprocess
        try:
            result = subprocess.run(
                ["xclip", "-o", "-selection", "clipboard"],
                capture_output=True, text=True
            )
            if result.returncode == 0 and result.stdout:
                html_content = result.stdout
            else:
                result = subprocess.run(
                    ["xsel", "-b", "-o"],
                    capture_output=True, text=True
                )
                if result.returncode == 0 and result.stdout:
                    html_content = result.stdout
                else:
                    print("Error: Could not read clipboard. Install xclip or xsel.", file=sys.stderr)
                    sys.exit(1)
        except FileNotFoundError:
            print("Error: Clipboard reading requires xclip or xsel", file=sys.stderr)
            sys.exit(1)
    elif args.file:
        html_content = open(args.file, "r").read()
    else:
        # Read from stdin
        if not sys.stdin.isatty():
            html_content = sys.stdin.read()
        else:
            print("Error: No input. Pipe HTML or provide a file.", file=sys.stderr)
            sys.exit(1)

    markdown = convert_string(html_content)
    print(markdown, end="")


if __name__ == "__main__":
    main()
