"""Curses-based interactive TUI for crypto-box."""

import os
import sys
import time
import curses
import textwrap
import threading
from . import (
    encrypt_file, decrypt_file,
    password_strength, password_strength_feedback,
    generate_totp_secret, totp,
    hash_file, hash_directory, checksum_verify,
    get_ssl_cert_info,
    colorize, __version__,
)

# ---------------------------------------------------------------------------
# TUI Helpers
# ---------------------------------------------------------------------------

THEME = {
    "title": curses.A_BOLD | curses.color_pair(1),
    "menu": curses.color_pair(2),
    "selected": curses.color_pair(3) | curses.A_REVERSE,
    "info": curses.color_pair(4),
    "error": curses.color_pair(5),
    "success": curses.color_pair(6),
    "warning": curses.color_pair(7),
    "normal": curses.color_pair(8),
    "input": curses.color_pair(4) | curses.A_BOLD,
}


def init_colors():
    curses.init_pair(1, curses.COLOR_CYAN, -1)       # title
    curses.init_pair(2, curses.COLOR_WHITE, -1)       # menu
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_CYAN)  # selected
    curses.init_pair(4, curses.COLOR_BLUE, -1)        # info
    curses.init_pair(5, curses.COLOR_RED, -1)         # error
    curses.init_pair(6, curses.COLOR_GREEN, -1)       # success
    curses.init_pair(7, curses.COLOR_YELLOW, -1)      # warning
    curses.init_pair(8, curses.COLOR_WHITE, -1)       # normal


def center_text(win, y, text, attr=0):
    h, w = win.getmaxyx()
    x = max(0, (w - len(text)) // 2)
    try:
        win.addstr(y, x, text[:w], attr)
    except curses.error:
        pass


def draw_header(win, title="crypto-box"):
    h, w = win.getmaxyx()
    try:
        win.attron(THEME["title"])
        center_text(win, 0, f" {title} v{__version__} ", curses.A_BOLD | curses.color_pair(1))
        win.attroff(THEME["title"])
        try:
            win.hline(1, 0, curses.ACS_HLINE, w)
        except curses.error:
            pass
    except curses.error:
        pass


def draw_footer(win, msg=""):
    h, w = win.getmaxyx()
    try:
        win.attron(curses.A_REVERSE)
        win.addstr(h - 1, 0, " " + msg + " " * (w - len(msg) - 1), curses.A_REVERSE)
        win.attroff(curses.A_REVERSE)
    except curses.error:
        pass


def input_field(win, y, x, prompt, default="", max_w=50):
    """Get user input in a curses window."""
    h, w = win.getmaxyx()
    try:
        win.addstr(y, x, prompt, THEME["input"])
        win.addstr(y, x + len(prompt), " " * max_w)
        curses.echo()
        win.move(y, x + len(prompt))
        result = win.getstr(y, x + len(prompt), max_w).decode("utf-8")
        curses.noecho()
        return result.strip() or default
    except curses.error:
        curses.noecho()
        return default


def show_message(win, y, msg, attr=THEME["info"], max_w=0):
    h, w = win.getmaxyx()
    if max_w == 0:
        max_w = w - 2
    try:
        win.addstr(y, 2, msg[:max_w], attr)
    except curses.error:
        pass


def wrap_lines(text, width):
    lines = []
    for paragraph in text.split("\n"):
        if paragraph.strip():
            lines.extend(textwrap.wrap(paragraph, width))
        else:
            lines.append("")
    return lines


# ---------------------------------------------------------------------------
# Menu System
# ---------------------------------------------------------------------------

class TUIApp:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.screen_height, self.screen_width = stdscr.getmaxyx()
        self.menu_items = [
            ("1", "File Encryption / Decryption", self.menu_encrypt),
            ("2", "Password Strength Checker", self.menu_password),
            ("3", "TOTP / OTP Generator", self.menu_totp),
            ("4", "Hash Files / Directories", self.menu_hash),
            ("5", "Verify Checksums", self.menu_checksum),
            ("6", "SSL Certificate Check", self.menu_ssl),
            ("7", "About / Help", self.menu_about),
            ("Q", "Quit", self.do_quit),
        ]
        self.running = True

    def run(self):
        curses.curs_set(0)
        self.stdscr.clear()
        self.stdscr.nodelay(0)
        while self.running:
            self.draw_main_menu()
            key = self.stdscr.getch()
            if key in (ord("q"), ord("Q")):
                break
            for label, _name, handler in self.menu_items:
                if key in (ord(label.upper()), ord(label.lower())):
                    self.stdscr.clear()
                    handler()
                    break

    def draw_main_menu(self):
        self.stdscr.clear()
        draw_header(self.stdscr, "CRYPTO-BOX - Security Toolkit")
        h, w = self.stdscr.getmaxyx()

        y = 4
        center_text(self.stdscr, y, "SELECT A TOOL", curses.A_BOLD)
        y += 2

        for label, name, _handler in self.menu_items:
            if label == "Q":
                y += 1
            text = f"  [{label}]  {name}"
            try:
                self.stdscr.addstr(y, max(0, (w - 30) // 2), text, THEME["menu"])
            except curses.error:
                pass
            y += 1

        y += 2
        center_text(self.stdscr, y, "Press number key to select, Q to quit", THEME["info"])
        self.stdscr.refresh()

    def wait_key(self, msg="Press any key to return to menu..."):
        draw_footer(self.stdscr, msg)
        self.stdscr.getch()

    def do_quit(self):
        self.running = False

    # -----------------------------------------------------------------------
    # 1. File Encryption
    # -----------------------------------------------------------------------
    def menu_encrypt(self):
        self.stdscr.clear()
        draw_header(self.stdscr, "File Encryption / Decryption")
        h, w = self.stdscr.getmaxyx()
        y = 3

        show_message(self.stdscr, y, "1) Encrypt a file  2) Decrypt a file  (ESC=back)", THEME["info"])
        y += 2
        key = self._get_choice()
        if key == ord("1"):
            self._do_encrypt()
        elif key == ord("2"):
            self._do_decrypt()
        else:
            return

    def _do_encrypt(self):
        self.stdscr.clear()
        draw_header(self.stdscr, "Encrypt File")
        h, w = self.stdscr.getmaxyx()
        y = 3

        f = self._ask_file(y, "Input file: ")
        if not f:
            return
        if not os.path.exists(f):
            show_message(self.stdscr, y + 6, f"File not found: {f}", THEME["error"])
            self.wait_key()
            return

        p = self._ask_password(y + 2, "Password: ")
        if not p:
            return

        out = f + ".enc"
        try:
            encrypt_file(f, out, p)
            show_message(self.stdscr, y + 6, f"Encrypted -> {out}", THEME["success"])
        except Exception as e:
            show_message(self.stdscr, y + 6, f"Error: {e}", THEME["error"])
        self.wait_key()

    def _do_decrypt(self):
        self.stdscr.clear()
        draw_header(self.stdscr, "Decrypt File")
        h, w = self.stdscr.getmaxyx()
        y = 3

        f = self._ask_file(y, "Input encrypted file: ")
        if not f:
            return
        if not os.path.exists(f):
            show_message(self.stdscr, y + 6, f"File not found: {f}", THEME["error"])
            self.wait_key()
            return

        p = self._ask_password(y + 2, "Password: ")
        if not p:
            return

        out = f.replace(".enc", ".dec", 1) if f.endswith(".enc") else f + ".dec"
        try:
            decrypt_file(f, out, p)
            show_message(self.stdscr, y + 6, f"Decrypted -> {out}", THEME["success"])
        except Exception as e:
            show_message(self.stdscr, y + 6, f"Error: {e}", THEME["error"])
        self.wait_key()

    # -----------------------------------------------------------------------
    # 2. Password Strength
    # -----------------------------------------------------------------------
    def menu_password(self):
        self.stdscr.clear()
        draw_header(self.stdscr, "Password Strength Checker")
        h, w = self.stdscr.getmaxyx()
        y = 3

        p = self._ask_password(y, "Enter password to check (hidden): ", echo=False)
        if not p:
            return

        score = password_strength(p)
        label = password_strength_feedback(score)

        bar_len = 30
        filled = int(score / 100 * bar_len)
        bar = "#" * filled + "-" * (bar_len - filled)

        show_message(self.stdscr, y + 2, f"Score: {score}/100", THEME["info"])
        show_message(self.stdscr, y + 3, f"[{bar}]", THEME["info"])

        color = THEME["success"] if score >= 60 else THEME["warning"] if score >= 40 else THEME["error"]
        show_message(self.stdscr, y + 5, f"Rating: {label}", color)
        show_message(self.stdscr, y + 7, f"Password length: {len(p)} chars", THEME["normal"])
        self.wait_key()

    # -----------------------------------------------------------------------
    # 3. TOTP
    # -----------------------------------------------------------------------
    def menu_totp(self):
        self.stdscr.clear()
        draw_header(self.stdscr, "TOTP / OTP Generator")
        h, w = self.stdscr.getmaxyx()
        y = 3

        show_message(self.stdscr, y, "1) Generate new secret  2) Get TOTP code  (ESC=back)", THEME["info"])
        y += 2
        key = self._get_choice()
        if key == ord("1"):
            secret = generate_totp_secret()
            self.stdscr.clear()
            draw_header(self.stdscr, "New TOTP Secret")
            show_message(self.stdscr, 3, "Copy this base32 secret:", THEME["info"])
            show_message(self.stdscr, 4, secret, curses.A_BOLD)
            se = self.stdscr.getch()
            if se == ord("q"):
                return
        elif key == ord("2"):
            secret = self._ask_string(3, "Base32 secret: ")
            if not secret:
                return
            self._show_totp_codes(secret)
        else:
            return

    def _show_totp_codes(self, secret):
        self.stdscr.clear()
        draw_header(self.stdscr, "TOTP Codes (live)")
        h, w = self.stdscr.getmaxyx()
        curses.curs_set(0)
        self.stdscr.nodelay(1)
        start = time.time()
        while True:
            try:
                code, remaining = totp(secret, 6, 30)
                self.stdscr.clear()
                draw_header(self.stdscr, "TOTP Codes (ESC to stop)")
                y = 3
                show_message(self.stdscr, y, f"Code: {code}", THEME["success"] | curses.A_BOLD)
                show_message(self.stdscr, y + 2, f"Expires in: {remaining}s", THEME["warning"])
                # Visual countdown bar
                bar_len = 20
                filled = int(remaining / 30 * bar_len)
                bar = "#" * filled + "-" * (bar_len - filled)
                show_message(self.stdscr, y + 3, f"[{bar}]", THEME["info"])
                self.stdscr.refresh()
                key = self.stdscr.getch()
                if key == 27:  # ESC
                    break
                time.sleep(0.5)
            except Exception as e:
                show_message(self.stdscr, y + 5, f"Error: {e}", THEME["error"])
                self.stdscr.refresh()
                time.sleep(2)
                break
        self.stdscr.nodelay(0)
        curses.curs_set(1)

    # -----------------------------------------------------------------------
    # 4. Hash
    # -----------------------------------------------------------------------
    def menu_hash(self):
        self.stdscr.clear()
        draw_header(self.stdscr, "Hash Files / Directories")
        h, w = self.stdscr.getmaxyx()
        y = 3

        path = self._ask_file(y, "File or directory path: ")
        if not path or not os.path.exists(path):
            if path:
                show_message(self.stdscr, y + 2, f"Not found: {path}", THEME["error"])
                self.wait_key()
            return

        algo = self._ask_choice(y + 2, "Algorithm (1=MD5 2=SHA1 3=SHA256 4=SHA512): ", "3")
        algo_map = {"1": "md5", "2": "sha1", "3": "sha256", "4": "sha512"}
        algo = algo_map.get(algo, "sha256")

        self.stdscr.clear()
        draw_header(self.stdscr, f"Hash Results ({algo.upper()})")
        y = 3

        try:
            if os.path.isdir(path):
                results = hash_directory(path, algo)
                for i, (fname, digest) in enumerate(sorted(results.items())[:100]):
                    if y >= h - 3:
                        show_message(self.stdscr, y, "... (truncated)", THEME["warning"])
                        break
                    show_message(self.stdscr, y, f"{digest}  {fname}", THEME["normal"])
                    y += 1
                show_message(self.stdscr, y + 1, f"Total: {len(results)} files hashed", THEME["success"])
            else:
                digest = hash_file(path, algo)
                show_message(self.stdscr, y, f"{digest}", curses.A_BOLD)
                show_message(self.stdscr, y + 1, path, THEME["info"])
        except Exception as e:
            show_message(self.stdscr, y, f"Error: {e}", THEME["error"])
        self.wait_key()

    # -----------------------------------------------------------------------
    # 5. Checksum Verify
    # -----------------------------------------------------------------------
    def menu_checksum(self):
        self.stdscr.clear()
        draw_header(self.stdscr, "Verify Checksums")
        h, w = self.stdscr.getmaxyx()
        y = 3

        f = self._ask_file(y, "Checksum file path: ")
        if not f or not os.path.exists(f):
            if f:
                show_message(self.stdscr, y + 2, f"File not found: {f}", THEME["error"])
                self.wait_key()
            return

        algo = self._ask_choice(y + 2, "Algorithm (1=MD5 2=SHA1 3=SHA256 4=SHA512): ", "3")
        algo_map = {"1": "md5", "2": "sha1", "3": "sha256", "4": "sha512"}
        algo = algo_map.get(algo, "sha256")

        self.stdscr.clear()
        draw_header(self.stdscr, "Checksum Verification")
        y = 3

        try:
            results = checksum_verify(f, algo)
            ok = sum(1 for r in results if r[2] == "OK")
            for fname, actual, status in results:
                if y >= h - 2:
                    break
                if status == "OK":
                    attr = THEME["success"]
                elif status == "MISSING":
                    attr = THEME["warning"]
                else:
                    attr = THEME["error"]
                show_message(self.stdscr, y, f"[{status:>7}]  {fname}", attr)
                y += 1
            y += 1
            total = len(results)
            attr = THEME["success"] if ok == total else THEME["error"]
            show_message(self.stdscr, y, f"{ok}/{total} passed", attr | curses.A_BOLD)
        except Exception as e:
            show_message(self.stdscr, y, f"Error: {e}", THEME["error"])
        self.wait_key()

    # -----------------------------------------------------------------------
    # 6. SSL Check
    # -----------------------------------------------------------------------
    def menu_ssl(self):
        self.stdscr.clear()
        draw_header(self.stdscr, "SSL Certificate Check")
        h, w = self.stdscr.getmaxyx()
        y = 3

        host = self._ask_string(y, "Hostname: ")
        if not host:
            return
        port_str = self._ask_string(y + 2, "Port (default 443): ")
        port = 443
        if port_str.strip():
            try:
                port = int(port_str.strip())
            except ValueError:
                pass

        # Show spinner / working
        self.stdscr.clear()
        draw_header(self.stdscr, f"Checking {host}:{port}...")
        self.stdscr.refresh()

        try:
            info = get_ssl_cert_info(host, port, timeout=10.0)
            self.stdscr.clear()
            draw_header(self.stdscr, f"SSL Certificate: {host}:{port}")
            y = 3

            for label, key in [("Subject", "subject"), ("Issuer", "issuer"),
                               ("Serial", "serialNumber"), ("Version", "version"),
                               ("Valid From", "notBefore"), ("Valid Until", "notAfter")]:
                val = info.get(key, "")
                if isinstance(val, dict):
                    val = str(val)
                show_message(self.stdscr, y, f"{label:>12}: {val}", THEME["normal"])
                y += 1

            days = info.get("daysRemaining")
            if days is not None:
                if info.get("isExpired"):
                    attr = THEME["error"]
                    label = "EXPIRED"
                elif days < 30:
                    attr = THEME["warning"]
                    label = f"{days} days remaining"
                else:
                    attr = THEME["success"]
                    label = f"{days} days remaining"
                show_message(self.stdscr, y, f"     Status: {label}", attr | curses.A_BOLD)
                y += 2

            show_message(self.stdscr, y, "Subject Alternative Names:", THEME["info"])
            y += 1
            for san in info.get("subjectAltName", [])[:10]:
                show_message(self.stdscr, y, f"  {san}", THEME["normal"])
                y += 1
        except Exception as e:
            show_message(self.stdscr, y, f"SSL check failed: {e}", THEME["error"])
        self.wait_key()

    # -----------------------------------------------------------------------
    # 7. About
    # -----------------------------------------------------------------------
    def menu_about(self):
        self.stdscr.clear()
        draw_header(self.stdscr, "About crypto-box")
        h, w = self.stdscr.getmaxyx()
        y = 3

        lines = [
            f"crypto-box v{__version__}",
            "All-in-one security toolkit",
            "Zero external dependencies (Python stdlib only)",
            "",
            "Features:",
            "  - File encryption/decryption (hashlib + XOR stream cipher)",
            "  - Password strength evaluation (0-100)",
            "  - TOTP/HOTP code generation (RFC 6238)",
            "  - Hash files/directories (MD5, SHA1, SHA256, SHA512)",
            "  - Checksum verification",
            "  - SSL certificate inspection (remote & local)",
            "",
            "Keyboard shortcuts:",
            "  ESC - Go back / Cancel",
            "  Q   - Quit to main menu or quit app",
            "",
            "Usage: crypto-box <command> [options]",
            "       crypto-box tui   (launch interactive TUI)",
        ]
        for line in lines:
            if not line:
                y += 1
                continue
            show_message(self.stdscr, y, line, THEME["normal"])
            y += 1
        self.wait_key()

    # -----------------------------------------------------------------------
    # Input helpers
    # -----------------------------------------------------------------------
    def _get_choice(self):
        y = self.screen_height - 1
        curses.curs_set(1)
        self.stdscr.move(y, 0)
        self.stdscr.clrtoeol()
        curses.echo()
        key = self.stdscr.getch()
        curses.noecho()
        curses.curs_set(0)
        return key

    def _ask_file(self, y, prompt):
        curses.curs_set(1)
        self.stdscr.move(y, 0)
        self.stdscr.clrtoeol()
        self.stdscr.addstr(y, 2, prompt, THEME["input"])
        curses.echo()
        f = self.stdscr.getstr(y, 2 + len(prompt), self.screen_width - len(prompt) - 4).decode("utf-8").strip()
        curses.noecho()
        curses.curs_set(0)
        f = os.path.expanduser(f)
        return f

    def _ask_password(self, y, prompt, echo=False):
        curses.curs_set(1)
        self.stdscr.move(y, 0)
        self.stdscr.clrtoeol()
        self.stdscr.addstr(y, 2, prompt, THEME["input"])
        if echo:
            curses.echo()
            p = self.stdscr.getstr(y, 2 + len(prompt), self.screen_width - len(prompt) - 4).decode("utf-8")
        else:
            curses.noecho()
            p = ""
            while True:
                ch = self.stdscr.getch()
                if ch in (10, 13, curses.KEY_ENTER):  # Enter
                    break
                elif ch == 27:  # ESC
                    curses.curs_set(0)
                    return ""
                elif ch == 127 or ch == curses.KEY_BACKSPACE:  # Backspace
                    if len(p) > 0:
                        p = p[:-1]
                        y_cur, x_cur = self.stdscr.getyx()
                        self.stdscr.addch(y_cur, x_cur - 1, " ")
                        self.stdscr.move(y_cur, x_cur - 1)
                elif 32 <= ch <= 126:  # printable
                    p += chr(ch)
                    self.stdscr.addch("*")
            self.stdscr.addstr("\n")
        curses.noecho()
        curses.curs_set(0)
        return p

    def _ask_string(self, y, prompt):
        curses.curs_set(1)
        self.stdscr.move(y, 0)
        self.stdscr.clrtoeol()
        self.stdscr.addstr(y, 2, prompt, THEME["input"])
        curses.echo()
        result = self.stdscr.getstr(y, 2 + len(prompt), self.screen_width - len(prompt) - 4).decode("utf-8").strip()
        curses.noecho()
        curses.curs_set(0)
        return result

    def _ask_choice(self, y, prompt, default="1"):
        curses.curs_set(1)
        self.stdscr.move(y, 0)
        self.stdscr.clrtoeol()
        self.stdscr.addstr(y, 2, prompt, THEME["input"])
        curses.echo()
        result = self.stdscr.getstr(y, 2 + len(prompt), 4).decode("utf-8").strip()
        curses.noecho()
        curses.curs_set(0)
        return result or default


def tui_main(stdscr):
    """Entry point for the TUI mode."""
    try:
        curses.cbreak()
        curses.noecho()
        curses.start_color()
        init_colors()
        app = TUIApp(stdscr)
        app.run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        curses.endwin()
        print(f"TUI error: {e}", file=sys.stderr)
        sys.exit(1)
