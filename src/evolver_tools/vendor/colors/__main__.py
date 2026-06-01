
import sys
import re

def hex_to_rgb(h):
    h = h.lstrip('#')
    if len(h) == 3:
        h = ''.join(c*2 for c in h)
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(r, g, b):
    return f'#{r:02x}{g:02x}{b:02x}'

def hsl_to_rgb(h, s, l):
    h = h / 360.0
    s = s / 100.0
    l = l / 100.0
    def hue2rgb(p, q, t):
        if t < 0: t += 1
        if t > 1: t -= 1
        if t < 1/6: return p + (q - p) * 6 * t
        if t < 1/2: return q
        if t < 2/3: return p + (q - p) * (2/3 - t) * 6
        return p
    if s == 0:
        r = g = b = l
    else:
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = hue2rgb(p, q, h + 1/3)
        g = hue2rgb(p, q, h)
        b = hue2rgb(p, q, h - 1/3)
    return (round(r*255), round(g*255), round(b*255))

def show_256():
    print("\n  256-color chart (bg):")
    for i in range(0, 16, 8):
        row = ''.join(f'\x1b[48;5;{i+j}m {i+j:>3} \x1b[0m' for j in range(8))
        print(f'  {row}')
    for block in range(16, 232, 36):
        print()
        for i in range(block, block+36, 6):
            row = ''.join(f'\x1b[48;5;{i+j}m {i+j:>3} \x1b[0m' for j in range(6) if i+j < 232)
            print(f'  {row}')
    print()
    print("  Grayscale (232-255):")
    row = ''.join(f'\x1b[48;5;{i}m {i:>3} \x1b[0m' for i in range(232, 256))
    print(f'  {row}')
    print('\x1b[0m')

def show_basic():
    print("\n  Basic 16 colors:")
    for i in range(8):
        fg = f'\x1b[38;5;{i}m'
        bg = f'\x1b[48;5;{i}m'
        bright = f'\x1b[38;5;{i+8}m'
        print(f'  {fg}Color {i}\x1b[0m  {bright}Color {i+8}\x1b[0m  {bg}        \x1b[0m')

def main():
    args = sys.argv[1:]
    if not args:
        show_basic()
        show_256()
        return
    
    cmd = args[0]
    
    if cmd == "256":
        show_256()
    elif cmd == "basic":
        show_basic()
    elif cmd in ("hex", "h") and len(args) >= 2:
        try:
            r, g, b = hex_to_rgb(args[1])
            h, s, v = 0, 0, 0
            print(f"HEX:    {args[1].lower()}")
            print(f"RGB:    {r}, {g}, {b}")
            print(f"\x1b[48;2;{r};{g};{b}m    Sample    \x1b[0m")
        except:
            print("Usage: colors hex #ff6600")
    elif cmd in ("rgb", "r") and len(args) >= 4:
        try:
            r, g, b = int(args[1]), int(args[2]), int(args[3])
            print(f"RGB:    {r}, {g}, {b}")
            print(f"HEX:    {rgb_to_hex(r, g, b)}")
            print(f"\x1b[48;2;{r};{g};{b}m    Sample    \x1b[0m")
        except:
            print("Usage: colors rgb 255 102 0")
    else:
        print("Usage: colors [hex|rgb|256|basic] [args...]")
        print("  colors           — show all color charts")
        print("  colors 256       — 256-color chart")
        print("  colors hex #ff0  — convert hex to RGB with preview")
        print("  colors rgb 255 102 0 — convert RGB to hex with preview")

if __name__ == "__main__":
    main()
