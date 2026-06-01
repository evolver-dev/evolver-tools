#!/usr/bin/env python3
"""ansi-to-html — Convert ANSI-colored terminal output to HTML."""
TOOL_META = {"name": "ansi-to-html", "func": "main", "desc": "Convert ANSI escape sequences to color HTML"}

import sys
import re

ANSI_COLORS = {
    "0": (0, 0, 0),
    "1": (128, 0, 0),
    "2": (0, 128, 0),
    "3": (128, 128, 0),
    "4": (0, 0, 128),
    "5": (128, 0, 128),
    "6": (0, 128, 128),
    "7": (192, 192, 192),
    "8": (128, 128, 128),
    "9": (255, 0, 0),
    "10": (0, 255, 0),
    "11": (255, 255, 0),
    "12": (0, 0, 255),
    "13": (255, 0, 255),
    "14": (0, 255, 255),
    "15": (255, 255, 255),
}

ANSI_STYLES = {
    "1": "font-weight:bold",
    "3": "font-style:italic",
    "4": "text-decoration:underline",
    "7": "background-color:#333;color:#fff",
    "9": "text-decoration:line-through",
}

ANSI_RE = re.compile(r"\x1b\[([\d;]*)m")


def ansi_to_html(text, dark=True):
    bg = "#1e1e1e" if dark else "#ffffff"
    fg = "#d4d4d4" if dark else "#000000"
    parts = ["<pre style='background:{};color:{};padding:8px;overflow:auto;font-family:monospace;line-height:1.4'>".format(bg, fg)]
    styles = []
    for segment in ANSI_RE.split(text):
        if not segment:
            continue
        if segment == "0":
            styles = []
            parts.append("</span>")
            continue
        if segment.isdigit() or ";" in segment:
            codes = segment.split(";")
            fg_color = None
            bg_color = None
            new_styles = []
            for c in codes:
                if c in ANSI_STYLES:
                    new_styles.append(ANSI_STYLES[c])
                elif c in ANSI_COLORS:
                    r, gg, b = ANSI_COLORS[c]
                    fg_color = f"rgb({r},{gg},{b})"
                elif c == "38" or c == "48":
                    # 256-color or truecolor - skip for simplicity
                    pass
            css = ";".join(new_styles)
            if fg_color:
                css = css + f";color:{fg_color}" if css else f"color:{fg_color}"
            if css:
                parts.append(f"<span style='{css}'>")
            continue
        # Escape HTML
        segment = segment.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        parts.append(segment)

    parts.append("</pre>")
    return "".join(parts)


def main():
    import sys, os

    args = sys.argv[1:]
    dark = True
    output = None
    files = []

    i = 0
    while i < len(args):
        if args[i] in ("-h", "--help"):
            print("Usage: ansi-to-html [options] [file...]")
            print("  -l, --light    Light background")
            print("  -o, --output FILE  Write to file (default: stdout)")
            print("  If no file, reads from stdin")
            return
        elif args[i] in ("-l", "--light"):
            dark = False
        elif args[i] in ("-o", "--output"):
            i += 1
            output = args[i] if i < len(args) else None
        else:
            files.append(args[i])
        i += 1

    if files:
        text = ""
        for f in files:
            with open(f) as fh:
                text += fh.read()
    else:
        text = sys.stdin.read()

    html = ansi_to_html(text, dark=dark)

    if output:
        with open(output, "w") as f:
            f.write(html)
        print(f"Written to {output}")
    else:
        sys.stdout.write(html)


if __name__ == "__main__":
    main()
