"""
net-analyzer TUI (Terminal UI) mode using curses.

Provides an interactive curses-based interface for running all network
analysis commands with real-time output display.
"""

import curses
import curses.textpad
import sys
import time
import threading
from typing import Optional

from . import cli

# ── Color pairs ───────────────────────────────────────────────────────────────
CP_HEADER = 1
CP_SUCCESS = 2
CP_ERROR = 3
CP_INFO = 4
CP_DIM = 5
CP_BANNER = 6
CP_INPUT = 7
CP_STATUS = 8


def _init_colors() -> None:
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(CP_HEADER, curses.COLOR_CYAN, -1)
    curses.init_pair(CP_SUCCESS, curses.COLOR_GREEN, -1)
    curses.init_pair(CP_ERROR, curses.COLOR_RED, -1)
    curses.init_pair(CP_INFO, curses.COLOR_YELLOW, -1)
    curses.init_pair(CP_DIM, curses.COLOR_WHITE, -1)  # dim pair — we'll use A_DIM
    curses.init_pair(CP_BANNER, curses.COLOR_MAGENTA, -1)
    curses.init_pair(CP_INPUT, curses.COLOR_YELLOW, -1)
    curses.init_pair(CP_STATUS, curses.COLOR_GREEN, -1)


# ── Menu items ────────────────────────────────────────────────────────────────
MENU_ITEMS = [
    ("Ping", "Ping a host"),
    ("Traceroute", "Trace route to host"),
    ("Port Scan", "Scan common ports"),
    ("DNS Lookup", "DNS resolution"),
    ("Whois", "Whois domain lookup"),
    ("Speedtest", "Download speed test"),
    ("All Checks", "Run all network checks"),
    ("Quit", "Exit program"),
]


def _draw_banner(stdscr: curses.window, y: int) -> int:
    """Draw the app banner, returns next y line."""
    banner = [
        "╔══════════════════════════════════════════╗",
        "║       net-analyzer  TUI Mode             ║",
        "║   Network Analysis Interactive Tool      ║",
        "╚══════════════════════════════════════════╝",
    ]
    for i, line in enumerate(banner):
        stdscr.attron(curses.color_pair(CP_BANNER) | curses.A_BOLD)
        stdscr.addstr(y + i, 2, line)
        stdscr.attroff(curses.color_pair(CP_BANNER) | curses.A_BOLD)
    return y + len(banner) + 1


def _draw_menu(stdscr: curses.window, y: int, selected: int) -> int:
    """Draw the menu, returns next y line."""
    stdscr.attron(curses.color_pair(CP_HEADER) | curses.A_BOLD)
    stdscr.addstr(y, 2, "MENU")
    stdscr.attroff(curses.color_pair(CP_HEADER) | curses.A_BOLD)
    y += 1

    for i, (item, desc) in enumerate(MENU_ITEMS):
        if i == selected:
            stdscr.attron(curses.color_pair(CP_INFO) | curses.A_REVERSE)
            stdscr.addstr(y, 4, f"▸ {item:18s}")
            stdscr.attroff(curses.color_pair(CP_INFO) | curses.A_REVERSE)
            stdscr.attron(curses.color_pair(CP_DIM) | curses.A_DIM)
            stdscr.addstr(y, 27, desc)
            stdscr.attroff(curses.color_pair(CP_DIM) | curses.A_DIM)
        else:
            stdscr.addstr(y, 4, f"  {item:18s}")
            stdscr.attron(curses.color_pair(CP_DIM) | curses.A_DIM)
            stdscr.addstr(y, 27, desc)
            stdscr.attroff(curses.color_pair(CP_DIM) | curses.A_DIM)
        y += 1

    y += 1
    stdscr.attron(curses.color_pair(CP_DIM) | curses.A_DIM)
    stdscr.addstr(y, 2, "↑↓ navigate   ↵ select   q quit   r refresh")
    stdscr.attroff(curses.color_pair(CP_DIM) | curses.A_DIM)
    return y + 2


def _draw_status(stdscr: curses.window, y: int, status: str) -> None:
    """Draw status line."""
    stdscr.attron(curses.color_pair(CP_STATUS))
    stdscr.addstr(y, 2, f"Status: {status}")
    stdscr.attroff(curses.color_pair(CP_STATUS))


def _draw_output(stdscr: curses.window, y: int, output: str) -> None:
    """Draw output text, stripping ANSI codes and wrapping."""
    max_y, max_x = stdscr.getmaxyx()
    # Strip ANSI codes that might have leaked through
    clean = cli.colorize_output(output, use_color=False)
    lines = clean.splitlines()

    for i, line in enumerate(lines):
        screen_y = y + i
        if screen_y >= max_y - 1:
            break
        # Truncate if too long
        if len(line) > max_x - 4:
            line = line[: max_x - 7] + "..."
        try:
            stdscr.addstr(screen_y, 4, line)
        except curses.error:
            pass


def _run_command(cmd_name: str, arg: str = "") -> str:
    """Run a CLI command and return its output."""
    try:
        if cmd_name == "Ping":
            host = arg or input("Host: ")
            return cli.cmd_ping(host, count=4)
        elif cmd_name == "Traceroute":
            host = arg or input("Host: ")
            return cli.cmd_trace(host)
        elif cmd_name == "Port Scan":
            host = arg or input("Host: ")
            return cli.cmd_scan(host)
        elif cmd_name == "DNS Lookup":
            domain = arg or input("Domain: ")
            return cli.cmd_dns(domain)
        elif cmd_name == "Whois":
            domain = arg or input("Domain: ")
            return cli.cmd_whois(domain)
        elif cmd_name == "Speedtest":
            size = arg or "10MB"
            return cli.cmd_speedtest(size)
        elif cmd_name == "All Checks":
            host = arg or input("Host: ")
            return cli.cmd_all(host)
        return f"Unknown command: {cmd_name}"
    except Exception as e:
        return f"Error: {e}"


class TUIApp:
    """Main TUI application class."""

    def __init__(self, stdscr: curses.window):
        self.stdscr = stdscr
        self.selected = 0
        self.output_text = ""
        self.last_result = ""
        self.status = "Ready"
        self.running = False
        self.input_buffer = ""
        self.edit_mode = False

    def run(self) -> None:
        """Main application loop."""
        curses.curs_set(0)
        self.stdscr.nodelay(True)
        self.stdscr.keypad(True)

        _init_colors()
        self._refresh_screen()

        while True:
            char = self.stdscr.getch()

            if char == -1:
                continue

            if char in (ord("q"), ord("Q")):
                break

            if char == curses.KEY_UP:
                self.selected = (self.selected - 1) % len(MENU_ITEMS)
                self._refresh_screen()

            elif char == curses.KEY_DOWN:
                self.selected = (self.selected + 1) % len(MENU_ITEMS)
                self._refresh_screen()

            elif char in (ord("\n"), ord("\r"), ord(" ")):
                item_name = MENU_ITEMS[self.selected][0]
                if item_name == "Quit":
                    break
                self._execute_command(item_name)

            elif char == ord("r"):
                self.output_text = ""
                self.last_result = ""
                self._refresh_screen()

    def _execute_command(self, item_name: str) -> None:
        """Execute the selected command."""
        self.status = f"Running {item_name}..."
        self.output_text = ""
        self._refresh_screen()

        # Prompt for argument if needed
        arg = ""
        needs_arg = item_name in ("Ping", "Traceroute", "Port Scan",
                                  "DNS Lookup", "Whois", "All Checks")
        if needs_arg:
            arg = self._get_input(f"Enter {item_name.lower()} target: ")
            if arg is None:  # cancelled
                self.status = "Cancelled"
                self._refresh_screen()
                return

        # Run command
        try:
            self.status = f"Running {item_name}..."
            self._refresh_screen()

            # Use threading with timeout for long commands
            result_container: list = []

            def _run():
                try:
                    result_container.append(_run_command(item_name, arg))
                except Exception as e:
                    result_container.append(f"Error: {e}")

            thread = threading.Thread(target=_run, daemon=True)
            thread.start()
            thread.join(timeout=30)

            if thread.is_alive():
                self.last_result = f"{cli.RED}Command timed out (30s){cli.RESET}"
            elif result_container:
                self.last_result = result_container[0]
            else:
                self.last_result = "No output"

            self.status = f"Done — press ↑↓ for another command, r to clear, q to quit"
            self._refresh_screen()

        except Exception as e:
            self.last_result = f"Error: {e}"
            self.status = "Error"
            self._refresh_screen()

    def _get_input(self, prompt: str) -> Optional[str]:
        """Show a text input prompt and return user input."""
        max_y, max_x = self.stdscr.getmaxyx()
        curses.curs_set(1)
        self.stdscr.nodelay(False)

        input_win = curses.newwin(3, max_x - 4, max_y // 2 - 1, 2)
        input_win.bkgd(" ")
        input_win.attron(curses.color_pair(CP_INPUT))
        input_win.box()
        input_win.attroff(curses.color_pair(CP_INPUT))

        input_win.attron(curses.A_BOLD)
        input_win.addstr(0, 2, f" {prompt} ")
        input_win.attroff(curses.A_BOLD)
        input_win.refresh()

        # Simple text input
        edit_win = curses.newwin(1, max_x - 10, max_y // 2, 4)
        edit_win.attron(curses.A_REVERSE)
        edit_win.addstr(0, 0, " " * (max_x - 12))
        edit_win.attroff(curses.A_REVERSE)
        edit_win.refresh()

        buffer = ""
        pos = 0

        while True:
            char = edit_win.getch()

            if char in (ord("\n"), ord("\r")):
                curses.curs_set(0)
                self.stdscr.nodelay(True)
                # Clear input windows
                input_win.clear()
                input_win.refresh()
                edit_win.clear()
                edit_win.refresh()
                curses.doupdate()
                return buffer.strip()

            elif char == 27:  # ESC
                curses.curs_set(0)
                self.stdscr.nodelay(True)
                input_win.clear()
                input_win.refresh()
                edit_win.clear()
                edit_win.refresh()
                curses.doupdate()
                return None

            elif char == curses.KEY_BACKSPACE or char == 127:
                if pos > 0:
                    buffer = buffer[:pos - 1] + buffer[pos:]
                    pos -= 1

            elif char == curses.KEY_DC:
                if pos < len(buffer):
                    buffer = buffer[:pos] + buffer[pos + 1:]

            elif char == curses.KEY_LEFT:
                if pos > 0:
                    pos -= 1

            elif char == curses.KEY_RIGHT:
                if pos < len(buffer):
                    pos += 1

            elif char == curses.KEY_HOME:
                pos = 0

            elif char == curses.KEY_END:
                pos = len(buffer)

            elif 32 <= char <= 126:
                buffer = buffer[:pos] + chr(char) + buffer[pos:]
                pos += 1

            # Redraw
            display = buffer[:max_x - 14]
            edit_win.clear()
            edit_win.attron(curses.A_REVERSE)
            edit_win.addstr(0, 0, display)
            edit_win.attroff(curses.A_REVERSE)
            edit_win.move(0, min(pos, max_x - 14))
            edit_win.refresh()

    def _refresh_screen(self) -> None:
        """Redraw the entire screen."""
        self.stdscr.clear()

        max_y, max_x = self.stdscr.getmaxyx()

        # Draw left panel (menu)
        y = _draw_banner(self.stdscr, 1)
        y = _draw_menu(self.stdscr, y, self.selected)

        # Draw status
        _draw_status(self.stdscr, y, self.status)

        # Draw output area (right side)
        output_x = max_x // 2
        if self.last_result:
            # Draw output header
            self.stdscr.attron(curses.color_pair(CP_HEADER) | curses.A_BOLD)
            header = " OUTPUT "
            self.stdscr.addstr(1, output_x, header)
            self.stdscr.attroff(curses.color_pair(CP_HEADER) | curses.A_BOLD)

            # Draw output content
            _draw_output(self.stdscr, 3, self.last_result)

        # Draw vertical divider
        divider_x = max_x // 2 - 1
        for row in range(max_y):
            try:
                self.stdscr.attron(curses.color_pair(CP_DIM) | curses.A_DIM)
                self.stdscr.addstr(row, divider_x, "│")
                self.stdscr.attroff(curses.color_pair(CP_DIM) | curses.A_DIM)
            except curses.error:
                pass

        self.stdscr.refresh()


def run_tui(stdscr: curses.window) -> None:
    """Entry point for curses TUI."""
    app = TUIApp(stdscr)
    try:
        app.run()
    except KeyboardInterrupt:
        pass


def main() -> None:
    """Launch TUI mode."""
    curses.wrapper(run_tui)


if __name__ == "__main__":
    main()
