#!/usr/bin/env python3
"""color-convert — Convert between color formats (hex, rgb, hsl, hsv, named)."""
TOOL_META = {"name": "color-convert", "func": "main", "desc": "Convert colors between hex/rgb/hsl/hsv/named formats"}

NAMED_COLORS = {
    "red": (255, 0, 0), "green": (0, 128, 0), "blue": (0, 0, 255),
    "white": (255, 255, 255), "black": (0, 0, 0), "gray": (128, 128, 128),
    "grey": (128, 128, 128), "yellow": (255, 255, 0), "orange": (255, 165, 0),
    "purple": (128, 0, 128), "pink": (255, 192, 203), "brown": (165, 42, 42),
    "cyan": (0, 255, 255), "magenta": (255, 0, 255), "lime": (0, 255, 0),
    "navy": (0, 0, 128), "teal": (0, 128, 128), "maroon": (128, 0, 0),
    "olive": (128, 128, 0), "silver": (192, 192, 192),
    "coral": (255, 127, 80), "tomato": (255, 99, 71), "gold": (255, 215, 0),
    "indigo": (75, 0, 130), "violet": (238, 130, 238),
}


def parse_hex(s):
    s = s.lstrip("#").strip()
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    return tuple(int(s[i:i+2], 16) for i in (0, 2, 4))


def to_hex(r, g, b):
    return f"#{r:02x}{g:02x}{b:02x}"


def to_rgb(r, g, b):
    return f"rgb({r},{g},{b})"


def rgb_to_hsl(r, g, b):
    r, g, b = r / 255, g / 255, b / 255
    mx, mn = max(r, g, b), min(r, g, b)
    l = (mx + mn) / 2
    if mx == mn:
        return (0, 0, round(l * 100))
    d = mx - mn
    s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
    if mx == r:
        h = (g - b) / d + (6 if g < b else 0)
    elif mx == g:
        h = (b - r) / d + 2
    else:
        h = (r - g) / d + 4
    h /= 6
    return (round(h * 360), round(s * 100), round(l * 100))


def hsl_to_rgb(h, s, l):
    h, s, l = h / 360, s / 100, l / 100
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
    return (round(r * 255), round(g * 255), round(b * 255))


def format_all(r, g, b):
    h, s, l = rgb_to_hsl(r, g, b)
    lines = [
        f"HEX:  {to_hex(r, g, b)}",
        f"RGB:  {to_rgb(r, g, b)}",
        f"HSL:  hsl({h},{s}%,{l}%)",
    ]
    # Find named
    for name, (nr, ng, nb) in NAMED_COLORS.items():
        if (nr, ng, nb) == (r, g, b):
            lines.append(f"Name: {name}")
            break
    return "\n".join(lines)


def main():
    import sys
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: color-convert <color>")
        print("Formats: #hex, rgb(r,g,b), hsl(h,s%,l%), or name")
        print("Examples:")
        print('  color-convert "#ff0000"')
        print("  color-convert rgb(255,0,0)")
        print("  color-convert red")
        print("  color-convert hsl(0,100%,50%)")
        return

    color = " ".join(args)
    r = g = b = None

    # Try named
    if color.lower() in NAMED_COLORS:
        r, g, b = NAMED_COLORS[color.lower()]

    # Try hex
    elif color.startswith("#"):
        try:
            r, g, b = parse_hex(color)
        except Exception:
            pass

    # Try rgb(r,g,b)
    elif color.startswith("rgb"):
        import re
        m = re.search(r"rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", color)
        if m:
            r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))

    # Try hsl(h,s,l)
    elif color.startswith("hsl"):
        import re
        m = re.search(r"hsl\s*\(\s*([\d.]+)\s*,\s*([\d.]+)%?\s*,\s*([\d.]+)%?", color)
        if m:
            r, g, b = hsl_to_rgb(float(m.group(1)), float(m.group(2)), float(m.group(3)))

    if r is None:
        print(f"Error: couldn't parse '{color}'", file=sys.stderr)
        sys.exit(1)

    print(format_all(r, g, b))


if __name__ == "__main__":
    main()
