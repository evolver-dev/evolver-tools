#!/usr/bin/env python3
"""figlet-cli — Display text as ASCII art fonts (built-in, no pyfiglet).

Usage: figlet-cli "Hello" [--font=block|banner|digital|mini|shadow]
       echo "World" | figlet-cli --font=block

Renders text in ASCII art fonts. Built-in fonts, zero external dependencies.
"""

import sys

FONTS = {}

def register_font(name):
    def decorator(fn):
        FONTS[name] = fn
        return fn
    return decorator

@register_font('block')
def render_block(text):
    lines = [''.join(f' {c} ' for c in text), ''.join(f'[{c}]' for c in text), ''.join(f' \u0305{c}\u0305 ' for c in text)]
    return '\n'.join(lines)

@register_font('banner')
def render_banner(text):
    """Simple banner font using # characters."""
    chars = {'A': [' ## ', '#  #', '####', '#  #', '#  #'],
             'B': ['### ', '#  #', '### ', '#  #', '### '],
             'C': [' ## ', '#  #', '#   ', '#  #', ' ## '],
             'D': ['### ', '#  #', '#  #', '#  #', '### '],
             'E': ['####', '#   ', '### ', '#   ', '####'],
             'F': ['####', '#   ', '### ', '#   ', '#   '],
             'G': [' ## ', '#  #', '# ##', '#  #', ' ###'],
             'H': ['#  #', '#  #', '####', '#  #', '#  #'],
             'I': ['###', ' # ', ' # ', ' # ', '###'],
             'J': ['  ##', '   #', '   #', '#  #', ' ## '],
             'K': ['#  #', '# # ', '##  ', '# # ', '#  #'],
             'L': ['#   ', '#   ', '#   ', '#   ', '####'],
             'M': ['#   #', '## ##', '# # #', '#   #', '#   #'],
             'N': ['#  #', '## #', '# ##', '#  #', '#  #'],
             'O': [' ## ', '#  #', '#  #', '#  #', ' ## '],
             'P': ['### ', '#  #', '### ', '#   ', '#   '],
             'Q': [' ## ', '#  #', '#  #', '# ##', ' ## '],
             'R': ['### ', '#  #', '### ', '# # ', '#  #'],
             'S': [' ###', '#   ', ' ## ', '   #', '### '],
             'T': ['#####', '  #  ', '  #  ', '  #  ', '  #  '],
             'U': ['#  #', '#  #', '#  #', '#  #', ' ## '],
             'V': ['#  #', '#  #', '#  #', ' # #', '  #  '],
             'W': ['#   #', '#   #', '# # #', '## ##', '#   #'],
             'X': ['#  #', ' # #', '  #  ', ' # #', '#  #'],
             'Y': ['#   #', ' # # ', '  #  ', ' #  ', '#   '],
             'Z': ['####', '   #', '  # ', ' #  ', '####'],
             '0': [' ## ', '#  #', '#  #', '#  #', ' ## '],
             '1': ['  # ', ' ## ', '  # ', '  # ', ' ###'],
             '2': [' ## ', '#  #', '  # ', ' #  ', '####'],
             '3': [' ###', '   #', '  # ', '   #', ' ###'],
             '4': ['#  #', '#  #', '####', '   #', '   #'],
             '5': ['####', '#   ', '### ', '   #', '### '],
             '6': [' ## ', '#   ', '### ', '#  #', ' ## '],
             '7': ['####', '   #', '  # ', ' #  ', '#   '],
             '8': [' ## ', '#  #', ' ## ', '#  #', ' ## '],
             '9': [' ## ', '#  #', ' ###', '   #', ' ## '],
             ' ': [' ', ' ', ' ', ' ', ' ']}
    result = []
    upper = text.upper()
    for row in range(5):
        line = ''
        for ch in upper:
            char_rows = chars.get(ch, chars[' '])
            line += char_rows[row] + ' '
        result.append(line)
    return '\n'.join(result)

@register_font('digital')
def render_digital(text):
    """7-segment digital display style."""
    seg_a = {'0': ' _ ', '1': '   ', '2': ' _ ', '3': ' _ ', '4': '   ',
             '5': ' _ ', '6': ' _ ', '7': ' _ ', '8': ' _ ', '9': ' _ '}
    seg_b = {'0': '| |', '1': '  |', '2': ' _|', '3': ' _|', '4': '|_|',
             '5': '|_ ', '6': '|_ ', '7': '  |', '8': '|_|', '9': '|_|'}
    seg_c = {'0': '|_|', '1': '  |', '2': '|_ ', '3': ' _|', '4': '  |',
             '5': ' _|', '6': '|_|', '7': '  |', '8': '|_|', '9': ' _|'}
    result = []
    upper = text.upper()
    row1 = ''.join(seg_a.get(c, '   ') for c in upper)
    row2 = ''.join(seg_b.get(c, '   ') for c in upper)
    row3 = ''.join(seg_c.get(c, '   ') for c in upper)
    return f'{row1}\n{row2}\n{row3}'

@register_font('mini')
def render_mini(text):
    """Minimal 2x2 font."""
    lines = []
    for ch in text:
        if ch.isalpha():
            lines.append(f' {ch} ')
        elif ch.isdigit():
            lines.append(f' {ch} ')
        else:
            lines.append('   ')
    return ' '.join(lines)

@register_font('shadow')
def render_shadow(text):
    """Shadow effect font."""
    result = []
    for ch in text:
        if ch.strip():
            result.append(f'{ch}{ch}')
        else:
            result.append('  ')
    return ''.join(result)

def main():
    args = sys.argv[1:]
    font = 'banner'

    for a in args:
        if a.startswith('--font='):
            font = a.split('=', 1)[1]
        elif a in ('-h', '--help'):
            print(__doc__)
            return

    text_args = [a for a in args if not a.startswith('-')]
    if text_args:
        text = ' '.join(text_args)
    elif not sys.stdin.isatty():
        text = sys.stdin.read().strip()
    else:
        print("Usage: figlet-cli <text> [--font=block|banner|digital|mini|shadow]")
        return

    if font in FONTS:
        print(FONTS[font](text))
    else:
        print(f"Unknown font: {font}")
        print(f"Available: {', '.join(FONTS.keys())}")

if __name__ == '__main__':
    main()
