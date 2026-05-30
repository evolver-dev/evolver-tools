#!/usr/bin/env python3
"""media-studio CLI — image metadata, QR code, ASCII art, banner, Morse code, figlet."""

import argparse
import hashlib
import json
import os
import struct
import sys
import textwrap
import time
from datetime import datetime

# ─── QR Code Generator (UTF-8 half-block) ───────────────────────────

_QR_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:"


def _qr_encode_numeric(data):
    bits = ""
    for c in data:
        if c.isdigit():
            v = ord(c) - 48
            bits += format(v, "04b")
    return bits


def _qr_encode_alphanumeric(data):
    bits = ""
    for c in data:
        v = _QR_ALPHABET.find(c.upper())
        if v >= 0:
            bits += format(v, "06b")
    return bits


def _qr_encode_byte(data):
    return "".join(format(b, "08b") for b in data.encode("utf-8"))


def _qr_make_data(data, ec_level="M"):
    if data.isdigit():
        mode = "numeric"
        mode_bits = "0001"
        data_bits = _qr_encode_numeric(data)
        char_count = len(data)
        char_count_bits = format(char_count, "010b")
    elif all(c.upper() in _QR_ALPHABET for c in data if c.isalnum() or c in " $%*+-./:"):
        mode = "alphanumeric"
        mode_bits = "0010"
        data_bits = _qr_encode_alphanumeric(data)
        char_count = len(data)
        char_count_bits = format(char_count, "009b")
    else:
        mode = "byte"
        mode_bits = "0100"
        data_bits = _qr_encode_byte(data)
        char_count = len(data)
        char_count_bits = format(char_count, "008b")

    # Simulate QR: just encode as bit string
    bit_stream = mode_bits + char_count_bits + data_bits
    # Pad to multiple of 8
    if len(bit_stream) % 8 != 0:
        bit_stream += "0" * (8 - len(bit_stream) % 8)
    # Add terminator if short
    return bit_stream


def _qr_render_pixel(matrix, x, y, size):
    """Draw a QR-like pixel using half-block characters."""
    on_top = "\u2588"  # Full block
    on_bottom = "\u2584"  # Lower half
    off = " "
    if y < size and matrix.get((x, y), 0):
        return on_top
    return off


def qr_generate(text, size=21):
    """Generate ASCII QR code from text."""
    data_bits = _qr_encode_byte(text)
    # Create a simple matrix
    size = min(max(len(text) * 2 + 17, 21), 41)
    if size > 41:
        size = 41

    matrix = {}
    # Fill finder patterns (corners)
    for corner_x, corner_y in [(0, 0), (size - 7, 0), (0, size - 7)]:
        for dx in range(7):
            for dy in range(7):
                is_border = (dx == 0 or dx == 6 or dy == 0 or dy == 6)
                is_inner = (2 <= dx <= 4 and 2 <= dy <= 4)
                matrix[(corner_x + dx, corner_y + dy)] = 1 if (is_border or is_inner) else 0

    # Fill data bits
    bit_idx = 0
    for y in range(size):
        for x in range(size):
            if (x, y) not in matrix and bit_idx < len(data_bits):
                matrix[(x, y)] = 1 if data_bits[bit_idx] == "1" else 0
                bit_idx += 1

    # Render
    lines = []
    header = "QR Code: " + text[:30] + ("..." if len(text) > 30 else "")
    lines.append(header)
    lines.append("")

    for y in range(0, size, 2):
        line = ""
        for x in range(size):
            top = matrix.get((x, y), 0)
            bottom = matrix.get((x, y + 1), 0) if y + 1 < size else 0
            if top and bottom:
                line += "\u2588"
            elif top:
                line += "\u2580"
            elif bottom:
                line += "\u2584"
            else:
                line += " "
        lines.append(line)

    lines.append("")
    lines.append(f"Size: {size}x{size}, Data: {len(data_bits)} bits")
    return "\n".join(lines)


# ─── ASCII Art Generator ────────────────────────────────────────────

_ASCII_STYLES = {
    "standard": "@%#*+=-:. ",
    "block": "\u2588\u2593\u2592\u2591 ",
    "dots": "@$%#*!;:,. ",
    "binary": "10",
    "squares": "\u2588\u25a0\u25e6\u25cb\u25c9 ",
    "gradient": "\u2593\u2592\u2591 ",
    "retro": "#&@%*+=!-:. ",
    "thick": "\u2588\u2589\u258A\u258B\u258C\u258D\u258E\u258F ",
}


def ascii_art(text, style="standard", width=80):
    """Convert text to ASCII art using character maps."""
    chars = _ASCII_STYLES.get(style, _ASCII_STYLES["standard"])
    lines = []
    # Simulate ASCII art by mapping characters to char density
    for line in text.split("\n"):
        if not line:
            lines.append("")
            continue
        result = ""
        for c in line:
            if c == " ":
                result += " "
            else:
                # Map char code to density index
                idx = (ord(c) % (len(chars) - 1))
                result += chars[idx]
        lines.append(result)
    return "\n".join(lines)


# ─── Banner Generator ──────────────────────────────────────────────

_BANNER_STYLES = ["simple", "double", "thick", "ascii"]


def banner(text, style="double", color=True):
    """Generate banner text in box frame styles."""
    lines = text.split("\n")
    max_len = max(len(l) for l in lines) if lines else 0

    if style == "simple":
        top = "+" + "-" * (max_len + 2) + "+"
        bottom = top
        side = "|"
    elif style == "double":
        top = "\u2554" + "\u2550" * (max_len + 2) + "\u2557"
        bottom = "\u255a" + "\u2550" * (max_len + 2) + "\u255d"
        side = "\u2551"
    elif style == "thick":
        top = "\u250f" + "\u2501" * (max_len + 2) + "\u2513"
        bottom = "\u2517" + "\u2501" * (max_len + 2) + "\u251b"
        side = "\u2503"
    elif style == "ascii":
        top = "#" * (max_len + 4)
        bottom = top
        side = "#"
    else:
        top = "+" + "-" * (max_len + 2) + "+"
        bottom = top
        side = "|"

    result = [top]
    for line in lines:
        result.append(f"{side} {line}{' ' * (max_len - len(line))} {side}")
    result.append(bottom)
    return "\n".join(result)


# ─── Morse Code Converter ──────────────────────────────────────────

_MORSE_CODE = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
    'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
    'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..', '0': '-----', '1': '.----', '2': '..---',
    '3': '...--', '4': '....-', '5': '.....', '6': '-....', '7': '--...',
    '8': '---..', '9': '----.', '.': '.-.-.-', ',': '--..--', '?': '..--..',
    "'": '.----.', '!': '-.-.--', '/': '-..-.', '(': '-.--.', ')': '-.--.-',
    '&': '.-...', ':': '---...', ';': '-.-.-.', '=': '-...-', '+': '.-.-.',
    '-': '-....-', '_': '..--.-', '"': '.-..-.', '$': '...-..-', '@': '.--.-.',
    ' ': '/',
}

_REVERSE_MORSE = {v: k for k, v in _MORSE_CODE.items()}


def text_to_morse(text):
    """Convert text to Morse code."""
    result = []
    for c in text.upper():
        if c in _MORSE_CODE:
            result.append(_MORSE_CODE[c])
        else:
            result.append("?")
    return " ".join(result)


def morse_to_text(morse):
    """Convert Morse code to text."""
    result = []
    for code in morse.split(" "):
        if code in _REVERSE_MORSE:
            result.append(_REVERSE_MORSE[code])
        elif code == "/":
            result.append(" ")
        elif code == "":
            continue
        else:
            result.append("?")
    return "".join(result)


# ─── Figlet-style ASCII ────────────────────────────────────────────

_FIGLET_FONTS = {
    "standard": {
        "A": ["  ███  ", " █░▒█  ", "█░▒░█  ", "█░░░█  ", "░███░  "],
        "B": ["████░  ", "█░░█░  ", "████░  ", "█░░█░  ", "████░  "],
        "C": [" ███░  ", "█░░░   ", "█      ", "█░░░   ", " ███░  "],
        "D": ["████░  ", "█░░█░  ", "█░░█░  ", "█░░█░  ", "████░  "],
        "E": ["█████░ ", "█      ", "████░  ", "█      ", "█████░ "],
        "F": ["█████░ ", "█      ", "████░  ", "█      ", "█      "],
        "G": [" ████░ ", "█      ", "█░██░  ", "█░░█░  ", "░███░  "],
        "H": ["█░░█░  ", "█░░█░  ", "████░  ", "█░░█░  ", "█░░█░  "],
        "I": ["█████░ ", "  █░   ", "  █░   ", "  █░   ", "█████░ "],
        "J": [" ████░ ", "   █░  ", "   █░  ", "█░░█░  ", "░██░   "],
        "K": ["█░░█░  ", "█░█░   ", "██░    ", "█░█░   ", "█░░█░  "],
        "L": ["█      ", "█      ", "█      ", "█      ", "█████░ "],
        "M": ["█░░░░█░", "██░░██░", "█░██░█░", "█░░░░█░", "█░░░░█░"],
        "N": ["█░░░░█░", "██░░░█░", "█░█░░█░", "█░░███░", "█░░░░█░"],
        "O": [" ███░  ", "█░░░█░ ", "█░░░█░ ", "█░░░█░ ", "░███░  "],
        "P": ["████░  ", "█░░█░  ", "████░  ", "█      ", "█      "],
        "Q": [" ███░  ", "█░░░█░ ", "█░░░█░ ", "█░███░ ", "░██░█░ "],
        "R": ["████░  ", "█░░█░  ", "████░  ", "█░█░   ", "█░░█░  "],
        "S": [" ████░ ", "█      ", " ███░  ", "    █░ ", "████░  "],
        "T": ["█████░ ", "  █░   ", "  █░   ", "  █░   ", "  █░   "],
        "U": ["█░░░█░ ", "█░░░█░ ", "█░░░█░ ", "█░░░█░ ", "░███░  "],
        "V": ["█░░░█░ ", "█░░░█░ ", "█░░░█░ ", "░█░█░  ", " ░█░   "],
        "W": ["█░░░░█░", "█░░░░█░", "█░█░█░", "█░█░█░", "░█░░█░ "],
        "X": ["█░░░█░ ", "░█░█░  ", " ░█░   ", "░█░█░  ", "█░░░█░ "],
        "Y": ["█░░░█░ ", "░█░█░  ", " ░█░   ", " ░█░   ", " ░█░   "],
        "Z": ["█████░ ", "   █░  ", "  █░   ", " █░    ", "█████░ "],
    },
}

_DEFAULT_FIGLET = ["     ", "     ", "     ", "     ", "     "]


def figlet(text, font="standard"):
    """Generate figlet-style ASCII art."""
    font_data = _FIGLET_FONTS.get(font, _FIGLET_FONTS["standard"])
    letters = []
    for c in text.upper():
        if c in font_data:
            letters.append(font_data[c])
        elif c == " ":
            letters.append(["     "] * 5)
        else:
            letters.append(_DEFAULT_FIGLET)

    if not letters:
        return text

    lines = []
    for row in range(5):
        line = ""
        for letter in letters:
            if row < len(letter):
                line += letter[row]
            else:
                line += "     "
        lines.append(line)

    return "\n".join(lines)


# ─── Image Metadata (EXIF parser via struct) ───────────────────────

def _read_jpeg_exif(path):
    """Parse JPEG EXIF metadata using struct."""
    info = {"File": path, "Size": os.path.getsize(path)}
    try:
        with open(path, "rb") as f:
            data = f.read()
    except Exception:
        return info

    # JPEG signature
    if data[:2] != b'\xff\xd8':
        info["Format"] = "Not JPEG"
        return info

    info["Format"] = "JPEG"
    info["Dimensions"] = _get_jpeg_dimensions(data)
    
    # Parse EXIF if present
    idx = data.find(b'Exif\x00\x00')
    if idx >= 0:
        info["EXIF"] = "Present"
        # Try to read basic tags
        tiff_offset = idx + 6
        try:
            endian = data[tiff_offset:tiff_offset + 2]
            if endian == b'II':
                bo = '<'
            elif endian == b'MM':
                bo = '>'
            else:
                return info
            
            ifd_offset = struct.unpack(bo + 'I', data[tiff_offset + 4:tiff_offset + 8])[0]
            entries = struct.unpack(bo + 'H', data[tiff_offset + ifd_offset:tiff_offset + ifd_offset + 2])[0]
            for i in range(min(entries, 20)):
                entry_start = tiff_offset + ifd_offset + 2 + i * 12
                tag = struct.unpack(bo + 'H', data[entry_start:entry_start + 2])[0]
                tag_names = {
                    0x010F: "Make", 0x0110: "Model", 0x0112: "Orientation",
                    0x0132: "DateTime", 0x8769: "ExifOffset",
                    0xA002: "PixelXDim", 0xA003: "PixelYDim",
                }
                if tag in tag_names:
                    info[tag_names[tag]] = f"tag:{tag}"
        except Exception:
            pass

    return info


def _get_jpeg_dimensions(data):
    """Extract JPEG dimensions from SOF marker."""
    idx = 0
    while idx < len(data):
        if data[idx] != 0xFF:
            break
        marker = data[idx + 1]
        if 0xC0 <= marker <= 0xCF and marker != 0xC4 and marker != 0xC8:
            try:
                height = struct.unpack('>H', data[idx + 5:idx + 7])[0]
                width = struct.unpack('>H', data[idx + 7:idx + 9])[0]
                return f"{width}x{height}"
            except Exception:
                return "Unknown"
        if marker == 0xD9:
            break
        try:
            length = struct.unpack('>H', data[idx + 2:idx + 4])[0]
            idx += 2 + length
        except Exception:
            break
    return "Unknown"


def image_meta(path):
    """Display image metadata."""
    if not os.path.isfile(path):
        return f"File not found: {path}"

    info = _read_jpeg_exif(path)
    lines = [f"Image Metadata: {path}", "=" * 60]
    for k, v in sorted(info.items()):
        lines.append(f"  {k:<20} {v}")
    return "\n".join(lines)


# ─── CLI Main ──────────────────────────────────────────────────────

def run_qr(args):
    text = " ".join(args) or "Hello, EVOLVER!"
    print(qr_generate(text))


def run_ascii(args):
    parser = argparse.ArgumentParser(prog="media-studio ascii")
    parser.add_argument("text", nargs="*", default=["Hello World"])
    parser.add_argument("--style", "-s", choices=list(_ASCII_STYLES.keys()), default="standard")
    args, _ = parser.parse_known_args()
    text = " ".join(args.text)
    print(ascii_art(text, args.style))


def run_banner(args):
    parser = argparse.ArgumentParser(prog="media-studio banner")
    parser.add_argument("text", nargs="*", default=["EVOLVER"])
    parser.add_argument("--style", "-s", choices=_BANNER_STYLES, default="double")
    args, _ = parser.parse_known_args()
    text = " ".join(args.text)
    print(banner(text, args.style))


def run_morse(args):
    parser = argparse.ArgumentParser(prog="media-studio morse")
    parser.add_argument("text", nargs="*", default=["SOS"])
    parser.add_argument("--decode", "-d", action="store_true")
    args, _ = parser.parse_known_args()
    text = " ".join(args.text)
    if args.decode:
        print(morse_to_text(text))
    else:
        print(text_to_morse(text))


def run_figlet(args):
    parser = argparse.ArgumentParser(prog="media-studio figlet")
    parser.add_argument("text", nargs="*", default=["EVOLVER"])
    parser.add_argument("--font", "-f", choices=list(_FIGLET_FONTS.keys()), default="standard")
    args, _ = parser.parse_known_args()
    text = " ".join(args.text)
    print(figlet(text, args.font))


def run_meta(args):
    if not args:
        print("Usage: media-studio meta <image_path>")
        return
    print(image_meta(args[0]))


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print(__doc__)
        return 0

    cmd = sys.argv[1]
    rest = sys.argv[2:]

    if cmd == "qr":
        run_qr(rest)
    elif cmd == "ascii":
        run_ascii(rest)
    elif cmd == "banner":
        run_banner(rest)
    elif cmd == "morse":
        run_morse(rest)
    elif cmd == "figlet":
        run_figlet(rest)
    elif cmd == "meta":
        run_meta(rest)
    elif cmd == "tui":
        try:
            from media_studio.tui import run_tui
            run_tui()
        except ImportError:
            print("TUI mode requires curses (not available in this environment)")
            return 1
    else:
        print(f"Unknown command: {cmd}")
        print("Try: media-studio help")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
