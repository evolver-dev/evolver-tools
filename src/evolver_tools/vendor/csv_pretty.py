#!/usr/bin/env python3
"""csv-pretty — Pretty-print CSV files as aligned tables with box-drawing characters.

Usage:
    csv-pretty data.csv
    cat data.csv | csv-pretty -w 120
    csv-pretty --style markdown data.csv
    csv-pretty --align center --no-header data.csv
"""
import sys
import csv
import os


def truncate(text, max_width):
    """Truncate text to max_width, adding … if truncated."""
    if max_width < 1:
        return ""
    text = str(text)
    if len(text) <= max_width:
        return text
    return text[: max_width - 1] + "…"


def align_text(text, width, alignment):
    """Align text within a given width."""
    if alignment == "left":
        return text.ljust(width)
    elif alignment == "right":
        return text.rjust(width)
    elif alignment == "center":
        return text.center(width)
    return text.ljust(width)


def build_table(rows, col_widths, alignment, style, has_header):
    """Render the table as a string."""
    lines = []

    # Determine box-drawing characters
    if style == "unicode":
        h_line = "─"
        v_line = "│"
        tl = "┌"
        tm = "┬"
        tr = "┐"
        ml = "├"
        mm = "┼"
        mr = "┤"
        bl = "└"
        bm = "┴"
        br = "┘"
    elif style == "ascii":
        h_line = "-"
        v_line = "|"
        tl = "+"
        tm = "+"
        tr = "+"
        ml = "+"
        mm = "+"
        mr = "+"
        bl = "+"
        bm = "+"
        br = "+"
    elif style == "markdown":
        h_line = "-"
        v_line = "|"
        tl = ""
        tm = ""
        tr = ""
        ml = ""
        mm = ""
        mr = ""
        bl = ""
        bm = ""
        br = ""

    num_cols = len(col_widths)

    def make_row(cells, left_end, sep, right_end):
        parts = []
        for i, cell in enumerate(cells):
            w = col_widths[i]
            parts.append(" " + align_text(truncate(cell, w), w, alignment) + " ")
        return left_end + sep.join(parts) + right_end

    def make_sep(left, mid, right):
        parts = []
        for w in col_widths:
            parts.append(h_line * (w + 2))
        return left + mid.join(parts) + right

    if style == "markdown":
        # Markdown table has no outer box, just pipes
        def md_row(cells):
            parts = []
            for i, cell in enumerate(cells):
                w = col_widths[i]
                parts.append(" " + align_text(truncate(cell, w), w, alignment) + " ")
            return "|" + "|".join(parts) + "|"

        if rows:
            lines.append(md_row(rows[0]))
        # Separator row
        sep_parts = []
        for w in col_widths:
            sep_parts.append(h_line * (w + 2))
        lines.append("|" + "|".join(sep_parts) + "|")
        for row in rows[1:]:
            lines.append(md_row(row))
        return "\n".join(lines)

    # Unicode / ASCII styles
    # Top border
    lines.append(make_sep(tl, tm, tr))

    for idx, row in enumerate(rows):
        lines.append(make_row(row, v_line, v_line, v_line))
        if idx == 0 and has_header and idx < len(rows) - 1:
            # Header separator
            lines.append(make_sep(ml, mm, mr))
        # No internal separators for no-header mode

    # Bottom border
    lines.append(make_sep(bl, bm, br))

    return "\n".join(lines)


def pretty_print_csv(
    filepath=None,
    max_width=80,
    alignment="left",
    no_header=False,
    style="unicode",
):
    """Read CSV and return pretty-printed table string."""
    # Read data
    if filepath:
        with open(filepath, "r", newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            raw_rows = list(reader)
    else:
        reader = csv.reader(sys.stdin)
        raw_rows = list(reader)

    if not raw_rows:
        return ""

    has_header = not no_header and len(raw_rows) >= 1

    # Separate header and data
    if has_header:
        header = raw_rows[0]
        data_rows = raw_rows[1:]
    else:
        header = None
        data_rows = raw_rows

    num_cols = max(len(header) if header else 0,
                   max((len(r) for r in data_rows), default=0))

    # Ensure all rows have the same number of cols
    def pad_row(row, n):
        return list(row) + [""] * (n - len(row))

    if header:
        header = pad_row(header, num_cols)
    data_rows = [pad_row(r, num_cols) for r in data_rows]

    # Calculate column widths
    col_widths = []
    for i in range(num_cols):
        widths = []
        if header:
            widths.append(len(str(header[i])))
        for row in data_rows:
            if i < len(row):
                widths.append(len(str(row[i])))
        # Clamp to max_width
        col_widths.append(min(max(widths, default=0), max_width))

    # Build rows
    display_rows = []
    if header:
        display_rows.append(header)
    display_rows.extend(data_rows)

    return build_table(display_rows, col_widths, alignment, style, has_header)


def main():
    # Manual arg parsing (zero dependencies)
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        doc = __doc__ or ""
        print(doc.strip())
        return

    max_width = 80
    alignment = "left"
    no_header = False
    style = "unicode"
    files = []

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("-w", "--width"):
            i += 1
            if i < len(args):
                try:
                    max_width = int(args[i])
                except ValueError:
                    print(f"Error: invalid width '{args[i]}'", file=sys.stderr)
                    sys.exit(1)
            else:
                print("Error: --width requires a value", file=sys.stderr)
                sys.exit(1)
        elif arg.startswith("--width="):
            try:
                max_width = int(arg.split("=", 1)[1])
            except ValueError:
                print(f"Error: invalid width '{arg}'", file=sys.stderr)
                sys.exit(1)
        elif arg in ("-a", "--align"):
            i += 1
            if i < len(args):
                val = args[i].lower()
                if val not in ("left", "right", "center"):
                    print(f"Error: invalid alignment '{val}' (use left, right, center)", file=sys.stderr)
                    sys.exit(1)
                alignment = val
            else:
                print("Error: --align requires a value", file=sys.stderr)
                sys.exit(1)
        elif arg.startswith("--align="):
            val = arg.split("=", 1)[1].lower()
            if val not in ("left", "right", "center"):
                print(f"Error: invalid alignment '{val}' (use left, right, center)", file=sys.stderr)
                sys.exit(1)
            alignment = val
        elif arg == "--no-header":
            no_header = True
        elif arg == "--style":
            i += 1
            if i < len(args):
                val = args[i].lower()
                if val not in ("unicode", "ascii", "markdown"):
                    print(f"Error: invalid style '{val}' (use unicode, ascii, markdown)", file=sys.stderr)
                    sys.exit(1)
                style = val
            else:
                print("Error: --style requires a value", file=sys.stderr)
                sys.exit(1)
        elif arg.startswith("--style="):
            val = arg.split("=", 1)[1].lower()
            if val not in ("unicode", "ascii", "markdown"):
                print(f"Error: invalid style '{val}' (use unicode, ascii, markdown)", file=sys.stderr)
                sys.exit(1)
            style = val
        elif arg.startswith("-"):
            print(f"Error: unknown option '{arg}'", file=sys.stderr)
            sys.exit(1)
        else:
            files.append(arg)
        i += 1

    # Determine input source
    if len(files) == 0:
        # Stdin mode
        text = pretty_print_csv(
            filepath=None,
            max_width=max_width,
            alignment=alignment,
            no_header=no_header,
            style=style,
        )
        if text:
            sys.stdout.write(text + "\n")
    elif len(files) == 1:
        filepath = files[0]
        if not os.path.isfile(filepath):
            print(f"Error: file not found: {filepath}", file=sys.stderr)
            sys.exit(1)
        text = pretty_print_csv(
            filepath=filepath,
            max_width=max_width,
            alignment=alignment,
            no_header=no_header,
            style=style,
        )
        if text:
            sys.stdout.write(text + "\n")
    else:
        # Multiple files with headers
        for filepath in files:
            if not os.path.isfile(filepath):
                print(f"Error: file not found: {filepath}", file=sys.stderr)
                sys.exit(1)
            print(f"=== {filepath} ===")
            text = pretty_print_csv(
                filepath=filepath,
                max_width=max_width,
                alignment=alignment,
                no_header=no_header,
                style=style,
            )
            if text:
                sys.stdout.write(text + "\n")
            print()


# === Auto-registration metadata ===
TOOL_META = {
    "name": "csv-pretty",
    "func": "main",
    "desc": "Pretty-print CSV files as aligned tables",
}

if __name__ == "__main__":
    main()
