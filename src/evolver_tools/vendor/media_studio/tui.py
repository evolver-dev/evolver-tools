#!/usr/bin/env python3
"""media-studio TUI — curses-based interactive media utility browser."""

import curses
import sys
import os
from .cli import (
    qr_generate, ascii_art, banner, text_to_morse, morse_to_text,
    figlet, image_meta, _ASCII_STYLES
)


_MENU_ITEMS = [
    ("QR Code", "Generate QR code from text"),
    ("ASCII Art", "8 styles of ASCII art"),
    ("Banner", "4 box-frame banner styles"),
    ("Morse Code", "Text ↔ Morse conversion"),
    ("Figlet", "Figlet-style ASCII art"),
    ("Image Metadata", "View JPEG EXIF data"),
    ("Help", "About media-studio"),
    ("Exit", "Return to shell"),
]


def run_tui():
    """Main TUI entry point."""
    try:
        curses.wrapper(_main_loop)
    except KeyboardInterrupt:
        pass


def _draw_menu(stdscr, selected):
    h, w = stdscr.getmaxyx()
    stdscr.clear()

    title = "═══ media-studio ═══"
    stdscr.addstr(0, max(0, (w - len(title)) // 2), title, curses.A_BOLD)

    for i, (name, desc) in enumerate(_MENU_ITEMS):
        y = 3 + i
        if i == selected:
            stdscr.attron(curses.A_REVERSE)
            stdscr.addstr(y, 4, f"  {name:<20}  ")
            stdscr.attroff(curses.A_REVERSE)
            stdscr.addstr(y, 28, f" {desc}")
        else:
            stdscr.addstr(y, 4, f"  {name:<20}  ")
            stdscr.addstr(y, 28, f" {desc}")

    stdscr.addstr(h - 2, 2, "↑↓ Navigate  Enter Select  q Quit  Esc Back", curses.A_DIM)
    stdscr.refresh()


def _text_input(stdscr, prompt, default=""):
    """Get text input from user."""
    curses.echo()
    stdscr.addstr(curses.LINES - 1, 0, prompt + " ")
    curses.curs_set(1)
    result = ""
    while True:
        c = stdscr.getch()
        if c == 10:  # Enter
            break
        elif c == 27:  # Esc
            result = ""
            break
        elif c == curses.KEY_BACKSPACE or c == 127:
            result = result[:-1]
        else:
            result += chr(c)
    curses.noecho()
    curses.curs_set(0)
    return result or default


def _show_result(stdscr, title, content):
    """Display result in a scrollable view."""
    h, w = stdscr.getmaxyx()
    lines = content.split("\n")
    offset = 0

    while True:
        stdscr.clear()
        stdscr.addstr(0, max(0, (w - len(title)) // 2), title, curses.A_BOLD)
        stdscr.addstr(1, 0, "─" * w, curses.A_DIM)

        max_lines = h - 4
        for i, line in enumerate(lines[offset:offset + max_lines]):
            if i + 2 < h:
                try:
                    stdscr.addstr(i + 2, 0, line[:w - 1])
                except Exception:
                    pass

        footer = f"Lines {offset + 1}-{min(offset + max_lines, len(lines))} of {len(lines)}"
        stdscr.addstr(h - 1, 0, footer[:w - 1], curses.A_DIM)
        stdscr.addstr(h - 1, max(0, w - 20), "↑↓ Scroll  q Back", curses.A_DIM)

        c = stdscr.getch()
        if c in (ord('q'), ord('Q'), 27):
            break
        elif c == curses.KEY_UP and offset > 0:
            offset -= 1
        elif c == curses.KEY_DOWN and offset + max_lines < len(lines):
            offset += 1
        elif c == curses.KEY_PPAGE:  # Page Up
            offset = max(0, offset - max_lines)
        elif c == curses.KEY_NPAGE:  # Page Down
            offset = min(len(lines) - max_lines, offset + max_lines)


def _handle_qr(stdscr):
    text = _text_input(stdscr, "QR Text: ", "Hello EVOLVER!")
    if text:
        result = qr_generate(text)
        _show_result(stdscr, "QR Code", result)


def _handle_ascii(stdscr):
    text = _text_input(stdscr, "ASCII Text: ", "EVOLVER")
    if text:
        styles_list = list(_ASCII_STYLES.keys())
        selected = 0
        while True:
            stdscr.clear()
            stdscr.addstr(0, 2, "Select ASCII Art Style:", curses.A_BOLD)
            for i, s in enumerate(styles_list):
                x = "> " if i == selected else "  "
                stdscr.addstr(2 + i, 4, f"{x}{s}")
            c = stdscr.getch()
            if c == curses.KEY_UP and selected > 0:
                selected -= 1
            elif c == curses.KEY_DOWN and selected < len(styles_list) - 1:
                selected += 1
            elif c in (10, ord(' ')):
                result = ascii_art(text, styles_list[selected])
                _show_result(stdscr, f"ASCII Art ({styles_list[selected]})", result)
                break
            elif c in (ord('q'), ord('Q'), 27):
                break


def _handle_banner(stdscr):
    text = _text_input(stdscr, "Banner Text: ", "EVOLVER")
    if text:
        styles = ["simple", "double", "thick", "ascii"]
        for s in styles:
            result = banner(text, s)
            _show_result(stdscr, f"Banner ({s})", result)
            if _text_input(stdscr, "Continue? (y/n): ", "y").lower() != "y":
                break


def _handle_morse(stdscr):
    text = _text_input(stdscr, "Text to convert: ", "SOS")
    if text:
        result = text_to_morse(text)
        _show_result(stdscr, "Text → Morse", result)
        # Also show decode
        decoded = morse_to_text(result)
        _show_result(stdscr, "Morse → Text (roundtrip)", decoded)


def _handle_figlet(stdscr):
    text = _text_input(stdscr, "Figlet Text: ", "EVOLVER")
    if text:
        result = figlet(text, "standard")
        _show_result(stdscr, "Figlet ASCII", result)


def _handle_meta(stdscr):
    path = _text_input(stdscr, "Image path: ", "")
    if path and os.path.isfile(path):
        result = image_meta(path)
        _show_result(stdscr, "Image Metadata", result)
    else:
        _show_result(stdscr, "Error", f"File not found: {path}")


def _show_help(stdscr):
    help_text = """media-studio v1.0.0

A CLI+TUI media utility toolkit with zero external dependencies.

Modules:
  QR Code     — Generate QR codes as ASCII art
  ASCII Art   — 8 character map styles
  Banner      — 4 box-frame styes (simple, double, thick, ascii)
  Morse Code  — Text to Morse code (and back)
  Figlet      — Figlet-style ASCII letter art
  Image Meta  — Read JPEG EXIF metadata

All modules work via Python stdlib only. No PIL, no external packages.

TUI Controls:
  ↑↓     Navigate menus / Scroll content
  Enter  Select menu item
  q/Q    Back / Quit
  Esc    Back to menu
  PgUp/PgDn  Page scroll

Author: EVOLVER
License: MIT"""
    _show_result(stdscr, "Help", help_text)


_HANDLERS = {
    0: _handle_qr,
    1: _handle_ascii,
    2: _handle_banner,
    3: _handle_morse,
    4: _handle_figlet,
    5: _handle_meta,
    6: _show_help,
}


def _main_loop(stdscr):
    curses.curs_set(0)
    curses.use_default_colors()
    selected = 0

    while True:
        _draw_menu(stdscr, selected)
        c = stdscr.getch()

        if c in (ord('q'), ord('Q'), 27):
            break
        elif c == curses.KEY_UP:
            selected = (selected - 1) % len(_MENU_ITEMS)
        elif c == curses.KEY_DOWN:
            selected = (selected + 1) % len(_MENU_ITEMS)
        elif c in (10, ord(' ')):  # Enter or Space
            if selected == 7:  # Exit
                break
            handler = _HANDLERS.get(selected)
            if handler:
                handler(stdscr)


if __name__ == "__main__":
    run_tui()
