#!/usr/bin/env python3
"""banner — Text banner generator (ASCII art)

Generate big text banners in various styles: block, slant, bubble, shadow.
No figlet required — pure Python.

Usage:
    banner "Hello World"                   # Default block style
    banner -s slant "Hello World"          # Slanted style
    banner -s bubble "Hello World"         # Bubble style
    banner -s shadow "Hello World"         # Shadow style
    banner -w 40 "Hello"                   # Max width 40
    banner -c red "Warning!"               # Colored output
    banner list                            # List available styles
"""
import sys


# Font definitions (simple ASCII art letters A-Z, 0-9)
FONTS = {}


def _make_block_font():
    """Create a simple block letter font (5 lines tall)."""
    font = {}
    letters = {
        'A': [
            '  A  ',
            ' A A ',
            'AAAAA',
            'A   A',
            'A   A',
        ],
        'B': [
            'BBBB ',
            'B   B',
            'BBBB ',
            'B   B',
            'BBBB ',
        ],
        'C': [
            ' CCC ',
            'C   C',
            'C    ',
            'C   C',
            ' CCC ',
        ],
        'D': [
            'DDDD ',
            'D   D',
            'D   D',
            'D   D',
            'DDDD ',
        ],
        'E': [
            'EEEEE',
            'E    ',
            'EEE  ',
            'E    ',
            'EEEEE',
        ],
        'F': [
            'FFFFF',
            'F    ',
            'FFF  ',
            'F    ',
            'F    ',
        ],
        'G': [
            ' GGG ',
            'G   G',
            'G    ',
            'G  GG',
            ' GGG ',
        ],
        'H': [
            'H   H',
            'H   H',
            'HHHHH',
            'H   H',
            'H   H',
        ],
        'I': [
            'IIIII',
            '  I  ',
            '  I  ',
            '  I  ',
            'IIIII',
        ],
        'J': [
            '  JJJ',
            '    J',
            '    J',
            'J   J',
            ' JJJ ',
        ],
        'K': [
            'K   K',
            'K  K ',
            'KKK  ',
            'K  K ',
            'K   K',
        ],
        'L': [
            'L    ',
            'L    ',
            'L    ',
            'L    ',
            'LLLLL',
        ],
        'M': [
            'M   M',
            'MM MM',
            'M M M',
            'M   M',
            'M   M',
        ],
        'N': [
            'N   N',
            'NN  N',
            'N N N',
            'N  NN',
            'N   N',
        ],
        'O': [
            ' OOO ',
            'O   O',
            'O   O',
            'O   O',
            ' OOO ',
        ],
        'P': [
            'PPPP ',
            'P   P',
            'PPPP ',
            'P    ',
            'P    ',
        ],
        'Q': [
            ' QQQ ',
            'Q   Q',
            'Q   Q',
            'Q  Q ',
            ' QQ Q',
        ],
        'R': [
            'RRRR ',
            'R   R',
            'RRRR ',
            'R  R ',
            'R   R',
        ],
        'S': [
            ' SSS ',
            'S   S',
            ' SSS ',
            '    S',
            'SSSS ',
        ],
        'T': [
            'TTTTT',
            '  T  ',
            '  T  ',
            '  T  ',
            '  T  ',
        ],
        'U': [
            'U   U',
            'U   U',
            'U   U',
            'U   U',
            ' UUU ',
        ],
        'V': [
            'V   V',
            'V   V',
            'V   V',
            ' V V ',
            '  V  ',
        ],
        'W': [
            'W   W',
            'W   W',
            'W W W',
            'W W W',
            ' W W ',
        ],
        'X': [
            'X   X',
            ' X X ',
            '  X  ',
            ' X X ',
            'X   X',
        ],
        'Y': [
            'Y   Y',
            ' Y Y ',
            '  Y  ',
            '  Y  ',
            '  Y  ',
        ],
        'Z': [
            'ZZZZZ',
            '   Z ',
            '  Z  ',
            ' Z   ',
            'ZZZZZ',
        ],
        '0': [
            ' 000 ',
            '0   0',
            '0 0 0',
            '0   0',
            ' 000 ',
        ],
        '1': [
            '  1  ',
            ' 11  ',
            '  1  ',
            '  1  ',
            '11111',
        ],
        '2': [
            ' 222 ',
            '2  2 ',
            '  2  ',
            ' 2   ',
            '22222',
        ],
        '3': [
            ' 333 ',
            '   3 ',
            '  33 ',
            '   3 ',
            ' 333 ',
        ],
        '4': [
            '4  4 ',
            '4  4 ',
            '44444',
            '   4 ',
            '   4 ',
        ],
        '5': [
            '55555',
            '5    ',
            '5555 ',
            '    5',
            '5555 ',
        ],
        '6': [
            ' 666 ',
            '6    ',
            '6666 ',
            '6   6',
            ' 666 ',
        ],
        '7': [
            '77777',
            '   7 ',
            '  7  ',
            ' 7   ',
            ' 7   ',
        ],
        '8': [
            ' 888 ',
            '8   8',
            ' 888 ',
            '8   8',
            ' 888 ',
        ],
        '9': [
            ' 999 ',
            '9   9',
            ' 9999',
            '    9',
            ' 999 ',
        ],
        ' ': [
            '     ',
            '     ',
            '     ',
            '     ',
            '     ',
        ],
        '!': [
            '  !  ',
            '  !  ',
            '  !  ',
            '     ',
            '  !  ',
        ],
        '?': [
            ' ??? ',
            '?   ?',
            '   ? ',
            '     ',
            '   ? ',
        ],
        '.': [
            '     ',
            '     ',
            '     ',
            '     ',
            '  .  ',
        ],
        ',': [
            '     ',
            '     ',
            '     ',
            '  ,  ',
            ' ,   ',
        ],
        ':': [
            '     ',
            '  :  ',
            '     ',
            '  :  ',
            '     ',
        ],
    }
    return letters


def _make_slant_font():
    """Simple italic/slanted style."""
    font = {}
    letters = _make_block_font()
    for ch, lines in letters.items():
        font[ch] = [' ' + line[:-1] if len(line) > 1 else line for line in lines]
    return font


def _make_bubble_font():
    """Bubble letter style."""
    font = {}
    base = _make_block_font()
    for ch, lines in base.items():
        result = []
        for line in lines:
            new_line = ''
            for c in line:
                if c == ' ':
                    new_line += ' '
                elif c.isalpha() or c.isdigit():
                    new_line += 'O' if c not in ' ' else ' '
                else:
                    new_line += c
            result.append(new_line)
        font[ch] = result
    return font


def _make_shadow_font():
    """Shadow style with 3D effect."""
    font = {}
    base = _make_block_font()
    for ch, lines in base.items():
        result = []
        for line in lines:
            # Add shadow offset with lighter characters
            shadowed = ''
            for c in line:
                if c == ' ':
                    shadowed += ' '
                elif c != ' ':
                    shadowed += c
            result.append(shadowed + ' ')
        # Add bottom shadow row
        shadow_row = ''
        for line in lines:
            last_char = line[-1] if line else ' '
            shadow_row += (last_char if last_char != ' ' else ' ') + ' '
        result.append(' ' + shadow_row[:-1])
        font[ch] = result
    return font


# Colors
COLORS = {
    'red': '\033[91m',
    'green': '\033[92m',
    'yellow': '\033[93m',
    'blue': '\033[94m',
    'magenta': '\033[95m',
    'cyan': '\033[96m',
    'white': '\033[97m',
    'bold': '\033[1m',
    'reset': '\033[0m',
}


def render(text, font='block', max_width=80, color=None):
    """Render text in specified font style."""
    font_data = FONTS.get(font, FONTS['block'])
    text = text.upper()

    # Build each line of the output
    lines_out = [''] * 5
    for ch in text:
        if ch in font_data:
            char_lines = font_data[ch]
            for i in range(5):
                lines_out[i] += char_lines[i] + '  '
        else:
            for i in range(5):
                lines_out[i] += ' ' * 5 + '  '

    # Apply color
    result = '\n'.join(lines_out)
    if color and color in COLORS:
        result = COLORS[color] + result + COLORS['reset']

    return result


def list_styles():
    """List available font styles."""
    print("Available styles:")
    for name in sorted(FONTS.keys()):
        print(f"  {name}")
    print()
    print("Available colors:", ', '.join(k for k in COLORS if k != 'reset'))


def main():
    global FONTS
    FONTS['block'] = _make_block_font()
    FONTS['slant'] = _make_slant_font()
    FONTS['bubble'] = _make_bubble_font()
    FONTS['shadow'] = _make_shadow_font()

    args = sys.argv[1:]

    if not args or args[0] in ('-h', '--help'):
        print(__doc__.strip())
        return

    if args[0] == 'list':
        list_styles()
        return

    style = 'block'
    max_width = 80
    color = None
    text_parts = []

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == '-s' or arg == '--style':
            i += 1
            if i < len(args):
                style = args[i]
        elif arg == '-w' or arg == '--width':
            i += 1
            if i < len(args):
                max_width = int(args[i])
        elif arg == '-c' or arg == '--color':
            i += 1
            if i < len(args):
                color = args[i]
        elif arg.startswith('-'):
            print(f"Error: unknown option '{arg}'", file=sys.stderr)
            sys.exit(1)
        else:
            text_parts.append(arg)
        i += 1

    if not text_parts:
        print("Error: no text provided", file=sys.stderr)
        sys.exit(1)

    text = ' '.join(text_parts)
    if style not in FONTS:
        print(f"Error: unknown style '{style}' (use 'banner list' for options)", file=sys.stderr)
        sys.exit(1)

    result = render(text, style, max_width, color)
    print(result)


if __name__ == '__main__':
    main()
