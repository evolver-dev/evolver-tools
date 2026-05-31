#!/usr/bin/env python3
"""markdown-format — Format and beautify Markdown tables and lists."""
TOOL_META = {"name": "markdown-format", "desc": "Format/beautify Markdown tables and lists", "func": "main"}

import sys
import re
import argparse


def format_table(table_text):
    """Format a Markdown table: align columns, pad cells."""
    lines = table_text.split("\n")
    if len(lines) < 2:
        return table_text

    rows = []
    for line in lines:
        line = line.strip()
        if not line or not line.startswith("|"):
            rows.append(line)
            continue
        cells = [c.strip() for c in line.split("|")]
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]
        rows.append(cells)

    # Find separator row
    sep_idx = None
    for i, row in enumerate(rows):
        if isinstance(row, list) and all(c.strip().replace("-", "").replace(":", "").strip() == "" for c in row):
            sep_idx = i
            break

    if sep_idx is None:
        # No separator found, not a real table
        return table_text

    # Calculate column widths
    col_count = 0
    for row in rows:
        if isinstance(row, list):
            col_count = max(col_count, len(row))

    widths = [0] * col_count
    alignments = ["left"] * col_count

    # Check separator row for alignment
    if isinstance(rows[sep_idx], list):
        for j, cell in enumerate(rows[sep_idx]):
            cell_stripped = cell.replace("-", "").replace(":", "").strip()
            if cell_stripped == "":
                if cell.startswith(":") and cell.endswith(":"):
                    alignments[j] = "center"
                elif cell.endswith(":"):
                    alignments[j] = "right"
                elif cell.startswith(":"):
                    alignments[j] = "left"

    for row in rows:
        if isinstance(row, list):
            for j, cell in enumerate(row):
                if j < col_count:
                    widths[j] = max(widths[j], len(cell))

    # Build formatted table
    result_lines = []

    # Header
    if sep_idx > 0 and isinstance(rows[0], list):
        header_cells = rows[0]
        result_lines.append(format_row(header_cells, widths, alignments))
        # Separator
        sep_cells = []
        for j in range(col_count):
            a = alignments[j] if j < len(alignments) else "left"
            w = widths[j] if j < len(widths) else 3
            if a == "center":
                sep_cells.append(":" + "-" * (w - 2) + ":")
            elif a == "right":
                sep_cells.append("-" * (w - 1) + ":")
            else:
                sep_cells.append("-" * w)
        result_lines.append(format_row(sep_cells, widths, alignments))

        # Data rows
        for i in range(1, sep_idx):
            if isinstance(rows[i], list):
                result_lines.append(format_row(rows[i], widths, alignments))

        for i in range(sep_idx + 1, len(rows)):
            if isinstance(rows[i], list):
                result_lines.append(format_row(rows[i], widths, alignments))
            else:
                result_lines.append(rows[i])
    else:
        for row in rows:
            if isinstance(row, list):
                result_lines.append(format_row(row, widths, alignments))
            else:
                result_lines.append(row)

    return "\n".join(result_lines)


def format_row(cells, widths, alignments):
    """Format a single row with proper padding."""
    parts = []
    for j, cell in enumerate(cells):
        w = widths[j] if j < len(widths) else len(cell)
        a = alignments[j] if j < len(alignments) else "left"
        if a == "right":
            parts.append(" " + cell.rjust(w))
        elif a == "center":
            total_pad = w - len(cell)
            left_pad = total_pad // 2
            right_pad = total_pad - left_pad
            parts.append(" " + " " * left_pad + cell + " " * right_pad)
        else:
            parts.append(" " + cell.ljust(w))
    return "|" + " |".join(parts) + " |"


def format_lists(text):
    """Normalize list indentation."""
    lines = text.split("\n")
    result = []
    for line in lines:
        # Normalize unordered list markers
        line = re.sub(r'^(\s*)[*\-\+]\s+', r'\1- ', line)
        # Normalize ordered list
        line = re.sub(r'^(\s*)\d+[.\)]\s+', r'\11. ', line)
        result.append(line)
    return "\n".join(result)


def format_markdown(text, tables=True, lists=True, code_blocks=True):
    """Apply all formatting operations."""
    if code_blocks:
        # Extract code blocks, process around them
        blocks = re.split(r'(```.*?```)', text, flags=re.DOTALL)
        result_parts = []
        for block in blocks:
            if block.startswith("```"):
                result_parts.append(block)
            else:
                if tables:
                    # Find table sections (lines starting with |)
                    lines = block.split("\n")
                    i = 0
                    while i < len(lines):
                        if lines[i].strip().startswith("|") and "|" in lines[i]:
                            table_lines = []
                            while i < len(lines) and lines[i].strip().startswith("|"):
                                table_lines.append(lines[i])
                                i += 1
                            result_parts.append(format_table("\n".join(table_lines)))
                        else:
                            result_parts.append(lines[i])
                            i += 1
                    block = "\n".join(result_parts)
                    result_parts = []
                if lists:
                    block = format_lists(block)
                result_parts.append(block)
        text = "".join(result_parts)
    else:
        if tables:
            lines = text.split("\n")
            result_parts = []
            i = 0
            while i < len(lines):
                if lines[i].strip().startswith("|") and "|" in lines[i]:
                    table_lines = []
                    while i < len(lines) and lines[i].strip().startswith("|"):
                        table_lines.append(lines[i])
                        i += 1
                    result_parts.append(format_table("\n".join(table_lines)))
                else:
                    result_parts.append(lines[i])
                    i += 1
            text = "\n".join(result_parts)
        if lists:
            text = format_lists(text)
    return text


def main():
    parser = argparse.ArgumentParser(
        description="Format and beautify Markdown tables and lists.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  markdown-format --file README.md
  cat doc.md | markdown-format
  markdown-format --no-lists --file doc.md
        """,
    )
    parser.add_argument("--file", "-f", help="Markdown file to format")
    parser.add_argument("--no-tables", action="store_true", help="Skip table formatting")
    parser.add_argument("--no-lists", action="store_true", help="Skip list formatting")
    parser.add_argument("--check", action="store_true",
                        help="Check mode: exit 1 if file would change")
    parser.add_argument("--inplace", "-i", action="store_true",
                        help="Modify file in place")
    args = parser.parse_args()

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            print(f"Error: file not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        content = sys.stdin.read()

    formatted = format_markdown(
        content,
        tables=not args.no_tables,
        lists=not args.no_lists,
    )

    if args.check:
        if content != formatted:
            print(f"File would change (not formatted)", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    if args.inplace and args.file:
        try:
            with open(args.file, "w", encoding="utf-8") as f:
                f.write(formatted)
        except Exception as e:
            print(f"Error writing: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(formatted, end="")


if __name__ == "__main__":
    main()
