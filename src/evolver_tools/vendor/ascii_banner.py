#!/usr/bin/env python3
"""ascii-banner — ASCII art banner generator.
Usage:  ascii-banner [--font=block|simple|wide|big] [--width=N] <text>
        echo text | ascii-banner [--font=...] [--width=N]

Four built-in fonts:
  block  – hash-filled block letters (#)
  simple – star-and-line outline letters (*)
  wide   – double-spaced block letters (wider)
  big    – uppercase geometric letters

Zero-dependency (stdlib only).
"""
import sys

# ── Font data ──────────────────────────────────────────────────────────
# Each font: {'A': ['row0','row1',...], ...}  (5 rows per char)
# Unknown chars render as blank columns of matching char width.

_BLOCK = {
    'A': ['  ###  ', ' #   # ', ' ##### ', ' #   # ', ' #   # '],
    'B': [' ####  ', ' #   # ', ' ####  ', ' #   # ', ' ####  '],
    'C': ['  #### ', ' #     ', ' #     ', ' #     ', '  #### '],
    'D': [' ####  ', ' #   # ', ' #   # ', ' #   # ', ' ####  '],
    'E': [' ##### ', ' #     ', ' ####  ', ' #     ', ' ##### '],
    'F': [' ##### ', ' #     ', ' ####  ', ' #     ', ' #     '],
    'G': ['  #### ', ' #     ', ' #  ## ', ' #   # ', '  ###  '],
    'H': [' #   # ', ' #   # ', ' ##### ', ' #   # ', ' #   # '],
    'I': [' ##### ', '   #   ', '   #   ', '   #   ', ' ##### '],
    'J': ['  #####', '    #  ', '    #  ', ' # #   ', '  ##   '],
    'K': [' #   # ', ' #  #  ', ' ###   ', ' #  #  ', ' #   # '],
    'L': [' #     ', ' #     ', ' #     ', ' #     ', ' ##### '],
    'M': [' ## ## ', ' #### #', ' # # # ', ' #   # ', ' #   # '],
    'N': [' ##  # ', ' ### # ', ' # ### ', ' #  ## ', ' #   # '],
    'O': ['  ###  ', ' #   # ', ' #   # ', ' #   # ', '  ###  '],
    'P': [' ####  ', ' #   # ', ' ####  ', ' #     ', ' #     '],
    'Q': ['  ###  ', ' #   # ', ' #   # ', ' #  #  ', '  ## # '],
    'R': [' ####  ', ' #   # ', ' ####  ', ' #  #  ', ' #   # '],
    'S': ['  #### ', ' #     ', '  ###  ', '     # ', ' ####  '],
    'T': [' ##### ', '   #   ', '   #   ', '   #   ', '   #   '],
    'U': [' #   # ', ' #   # ', ' #   # ', ' #   # ', '  ###  '],
    'V': [' #   # ', ' #   # ', ' #   # ', '  # #  ', '   #   '],
    'W': [' #   # ', ' #   # ', ' # # # ', ' #### #', ' ## ## '],
    'X': [' #   # ', '  # #  ', '   #   ', '  # #  ', ' #   # '],
    'Y': [' #   # ', '  # #  ', '   #   ', '   #   ', '   #   '],
    'Z': [' ##### ', '    #  ', '   #   ', '  #    ', ' ##### '],
    ' ': ['      ', '      ', '      ', '      ', '      '],
    '!': ['   #   ', '   #   ', '   #   ', '       ', '   #   '],
    '.': ['       ', '       ', '       ', '       ', '   #   '],
    ',': ['       ', '       ', '       ', '   #   ', '  #    '],
    '?': ['  ###  ', '     # ', '   #   ', '       ', '   #   '],
    '0': ['  ###  ', ' #  ## ', ' # # # ', ' ##  # ', '  ###  '],
    '1': ['   #   ', '  ##   ', '   #   ', '   #   ', ' ##### '],
    '2': ['  ###  ', '     # ', '  ###  ', ' #     ', ' ##### '],
    '3': ['  ###  ', '     # ', '  ###  ', '     # ', '  ###  '],
    '4': [' #   # ', ' #   # ', ' ##### ', '     # ', '     # '],
    '5': [' ##### ', ' #     ', '  #### ', '     # ', ' ####  '],
    '6': ['  #### ', ' #     ', ' ####  ', ' #   # ', '  ###  '],
    '7': [' ##### ', '     # ', '    #  ', '   #   ', '   #   '],
    '8': ['  ###  ', ' #   # ', '  ###  ', ' #   # ', '  ###  '],
    '9': ['  ###  ', ' #   # ', '  #### ', '     # ', ' ####  '],
}

_SIMPLE = {
    'A': ['  ***  ', ' *   * ', ' ***** ', ' *   * ', ' *   * '],
    'B': [' ****  ', ' *   * ', ' ****  ', ' *   * ', ' ****  '],
    'C': ['  **** ', ' *     ', ' *     ', ' *     ', '  **** '],
    'D': [' ****  ', ' *   * ', ' *   * ', ' *   * ', ' ****  '],
    'E': [' ***** ', ' *     ', ' ***   ', ' *     ', ' ***** '],
    'F': [' ***** ', ' *     ', ' ***   ', ' *     ', ' *     '],
    'G': ['  **** ', ' *     ', ' *  ** ', ' *   * ', '  ***  '],
    'H': [' *   * ', ' *   * ', ' ***** ', ' *   * ', ' *   * '],
    'I': [' ***** ', '   *   ', '   *   ', '   *   ', ' ***** '],
    'J': ['  *****', '    *  ', '    *  ', ' * *   ', '  **   '],
    'K': [' *   * ', ' *  *  ', ' ***   ', ' *  *  ', ' *   * '],
    'L': [' *     ', ' *     ', ' *     ', ' *     ', ' ***** '],
    'M': [' ** ** ', ' ***** ', ' * * * ', ' *   * ', ' *   * '],
    'N': [' **  * ', ' *** * ', ' * *** ', ' *  ** ', ' *   * '],
    'O': ['  ***  ', ' *   * ', ' *   * ', ' *   * ', '  ***  '],
    'P': [' ****  ', ' *   * ', ' ****  ', ' *     ', ' *     '],
    'Q': ['  ***  ', ' *   * ', ' * * * ', ' *  *  ', '  ** * '],
    'R': [' ****  ', ' *   * ', ' ****  ', ' *  *  ', ' *   * '],
    'S': ['  **** ', ' *     ', '  ***  ', '     * ', ' ****  '],
    'T': [' ***** ', '   *   ', '   *   ', '   *   ', '   *   '],
    'U': [' *   * ', ' *   * ', ' *   * ', ' *   * ', '  ***  '],
    'V': [' *   * ', ' *   * ', ' *   * ', '  * *  ', '   *   '],
    'W': [' *   * ', ' *   * ', ' * * * ', ' ***** ', ' ** ** '],
    'X': [' *   * ', '  * *  ', '   *   ', '  * *  ', ' *   * '],
    'Y': [' *   * ', '  * *  ', '   *   ', '   *   ', '   *   '],
    'Z': [' ***** ', '    *  ', '   *   ', '  *    ', ' ***** '],
    ' ': ['      ', '      ', '      ', '      ', '      '],
    '!': ['   *   ', '   *   ', '   *   ', '       ', '   *   '],
    '.': ['       ', '       ', '       ', '       ', '   *   '],
    '?': ['  ***  ', '     * ', '   *   ', '       ', '   *   '],
    '0': ['  ***  ', ' *  ** ', ' * * * ', ' **  * ', '  ***  '],
    '1': ['   *   ', '  **   ', '   *   ', '   *   ', ' ***** '],
    '2': ['  ***  ', '     * ', '  ***  ', ' *     ', ' ***** '],
    '3': ['  ***  ', '     * ', '  ***  ', '     * ', '  ***  '],
    '4': [' *   * ', ' *   * ', ' ***** ', '     * ', '     * '],
    '5': [' ***** ', ' *     ', '  **** ', '     * ', ' ****  '],
    '6': ['  **** ', ' *     ', ' ****  ', ' *   * ', '  ***  '],
    '7': [' ***** ', '     * ', '    *  ', '   *   ', '   *   '],
    '8': ['  ***  ', ' *   * ', '  ***  ', ' *   * ', '  ***  '],
    '9': ['  ***  ', ' *   * ', '  **** ', '     * ', ' ****  '],
}

# Wide font: double-spaced block (each row repeated horizontally)
_WIDE = {k: [r.replace(' ', '  ').replace('#', '##') for r in v]
         for k, v in _BLOCK.items()}

# Big font: uppercase geometric letters using hash
_BIG = {
    'A': ['  #####  ', ' ##   ## ', ' ##   ## ', ' ####### ', ' ##   ## ', ' ##   ## ', ' ##   ## '],
    'B': [' ######  ', ' ##   ## ', ' ######  ', ' ##   ## ', ' ######  '],
    'C': ['  ###### ', ' ##      ', ' ##      ', ' ##      ', ' ###### '],
    'D': [' ######  ', ' ##   ## ', ' ##   ## ', ' ##   ## ', ' ######  '],
    'E': [' ####### ', ' ##      ', ' ######  ', ' ##      ', ' ####### '],
    'F': [' ####### ', ' ##      ', ' ######  ', ' ##      ', ' ##      '],
    'G': ['  ###### ', ' ##      ', ' ##  ### ', ' ##   ## ', '  #####  '],
    'H': [' ##   ## ', ' ##   ## ', ' ####### ', ' ##   ## ', ' ##   ## '],
    'I': ['  #####  ', '   ###   ', '   ###   ', '   ###   ', '  #####  '],
    'J': ['   ##### ', '    ##   ', '    ##   ', ' ## ##   ', '  ###    '],
    'K': [' ##   ## ', ' ##  ##  ', ' #####   ', ' ##  ##  ', ' ##   ## '],
    'L': [' ##      ', ' ##      ', ' ##      ', ' ##      ', ' ####### '],
    'M': [' ### ### ', ' ###### #', ' ## # ## ', ' ##   ## ', ' ##   ## '],
    'N': [' ###  ## ', ' ##### # ', ' ## #### ', ' ##  ### ', ' ##   ## '],
    'O': ['  #####  ', ' ##   ## ', ' ##   ## ', ' ##   ## ', '  #####  '],
    'P': [' ######  ', ' ##   ## ', ' ######  ', ' ##      ', ' ##      '],
    'Q': ['  #####  ', ' ##   ## ', ' ##   ## ', ' ## ###  ', '  ### ## '],
    'R': [' ######  ', ' ##   ## ', ' ######  ', ' ##  ##  ', ' ##   ## '],
    'S': ['  ###### ', ' ##      ', '  #####  ', '      ## ', ' ######  '],
    'T': [' ####### ', '   ###   ', '   ###   ', '   ###   ', '   ###   '],
    'U': [' ##   ## ', ' ##   ## ', ' ##   ## ', ' ##   ## ', '  #####  '],
    'V': [' ##   ## ', ' ##   ## ', ' ##   ## ', '  ## ##  ', '   ###   '],
    'W': [' ##   ## ', ' ##   ## ', ' ## # ## ', ' ###### #', ' ### ### '],
    'X': [' ##   ## ', '  ## ##  ', '   ###   ', '  ## ##  ', ' ##   ## '],
    'Y': [' ##   ## ', '  ## ##  ', '   ###   ', '   ###   ', '   ###   '],
    'Z': [' ####### ', '     ##  ', '    ##   ', '   ##    ', ' ####### '],
    ' ': ['        ', '        ', '        ', '        ', '        '],
    '!': ['   ##   ', '   ##   ', '   ##   ', '        ', '   ##   '],
    '.': ['        ', '        ', '        ', '        ', '   ##   '],
    '?': ['  ##### ', '      ##', '    ### ', '        ', '    ##  '],
    '0': ['  ##### ', ' ##  ###', ' ## # ##', ' ###  ##', '  ##### '],
    '1': ['   ###  ', '  ####  ', '   ###  ', '   ###  ', ' #######'],
    '2': ['  ##### ', '      ##', '   #### ', '  ##    ', ' #######'],
    '3': ['  ##### ', '      ##', '   #### ', '      ##', '  ##### '],
    '4': [' ##   ##', ' ##   ##', ' ########', '      ##', '      ##'],
    '5': [' ########', ' ##      ', '  #######', '       ##', ' ########'],
    '6': ['   #####', '  ##     ', '  ###### ', '  ##   ##', '   ####  '],
    '7': [' #######', '     ## ', '    ##   ', '   ##    ', '   ##    '],
    '8': ['  ##### ', ' ##   ## ', '  ##### ', ' ##   ## ', '  ##### '],
    '9': ['  ##### ', ' ##   ## ', '  ###### ', '     ##  ', ' #####  '],
}

FONTS = {
    'block': _BLOCK,
    'simple': _SIMPLE,
    'wide': _WIDE,
    'big': _BIG,
}


def get_char_width(font_name):
    """Return the width of a single character in the given font."""
    font = FONTS.get(font_name, _BLOCK)
    for data in font.values():
        if data:
            return len(data[0])
    return 6  # fallback


def generate_banner(text, font_name='block'):
    """Render text using the named font. Returns list of row strings."""
    font = FONTS.get(font_name, _BLOCK)
    rows = max(len(v) for v in font.values()) if font else 5
    result = ['' for _ in range(rows)]
    for ch in text.upper():
        if ch in font:
            for i, row in enumerate(font[ch]):
                result[i] += row
        else:
            w = get_char_width(font_name)
            for i in range(rows):
                result[i] += ' ' * w
    return result


def wrap_banner(banner_rows, width):
    """Wrap banner lines that exceed width into multiple blocks."""
    if not banner_rows:
        return banner_rows
    line_len = len(banner_rows[0])
    if line_len <= width:
        return banner_rows
    # Chunk every banner row into pieces and stack vertically
    chunk_size = width
    num_chunks = (line_len + chunk_size - 1) // chunk_size
    wrapped = []
    for ci in range(num_chunks):
        start = ci * chunk_size
        end = min(start + chunk_size, line_len)
        for row in banner_rows:
            piece = row[start:end]
            # Padded to chunk_size for alignment
            piece = piece.ljust(chunk_size)
            wrapped.append(piece)
    return wrapped


def print_banner(text, font_name='block', width=None):
    """Render and print a banner."""
    if not text:
        return
    banner_rows = generate_banner(text, font_name)
    if width and width > 0:
        banner_rows = wrap_banner(banner_rows, width)
    for row in banner_rows:
        print(row.rstrip())


def list_fonts():
    """Print available fonts."""
    print("Available fonts:")
    for name in sorted(FONTS):
        desc = {
            'block': 'hash-filled block letters (#)',
            'simple': 'star-and-line outline letters (*)',
            'wide': 'double-spaced block letters',
            'big': 'uppercase geometric letters (7-row)',
        }.get(name, '')
        print(f"  {name:<10} {desc}")


def main():
    args = sys.argv[1:]

    # Parse --font and --width manually (stdlib only, no argparse)
    font_name = 'block'
    width = None
    text_args = []

    i = 0
    while i < len(args):
        a = args[i]
        if a == '--font' and i + 1 < len(args):
            font_name = args[i + 1]
            i += 2
        elif a.startswith('--font='):
            font_name = a.split('=', 1)[1]
            i += 1
        elif a == '--width' and i + 1 < len(args):
            try:
                width = int(args[i + 1])
            except ValueError:
                pass
            i += 2
        elif a.startswith('--width='):
            try:
                width = int(a.split('=', 1)[1])
            except ValueError:
                pass
            i += 1
        elif a == '--list':
            list_fonts()
            return
        elif a == '--help' or a == '-h':
            print(__doc__.strip())
            return
        else:
            text_args.append(a)
            i += 1

    # Check font name
    if font_name not in FONTS:
        print(f"Unknown font '{font_name}'. Use --list to see available fonts.", file=sys.stderr)
        sys.exit(1)

    # Get text: positional args or stdin
    if text_args:
        text = ' '.join(text_args)
    else:
        stdin_data = sys.stdin.read() if sys.stdin is not None else ''
        text = stdin_data.strip()

    if not text:
        print("Usage: banner [--font=NAME] [--width=N] [--list] <text>", file=sys.stderr)
        print("       echo text | banner [--font=NAME] [--width=N]", file=sys.stderr)
        sys.exit(1)

    print_banner(text, font_name, width)


TOOL_META = {"name": "ascii-banner", "func": "main", "desc": "ASCII art banner generator — block, simple, wide, big fonts"}

if __name__ == '__main__':
    main()
