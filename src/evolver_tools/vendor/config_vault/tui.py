"""config-vault TUI module.

Curses-based interactive config file viewer and editor.
Supports .env, JSON, YAML, and TOML formats.
"""

import curses
import json
import os
import sys
import textwrap
from typing import Any, Dict, List, Optional, Tuple

from .cli import (
    _color,
    _die,
    _err,
    _ok,
    _warn,
    _detect_format,
    _parse_env,
    _serialize_env,
    _parse_yaml_simple,
    _serialize_yaml_simple,
    _parse_toml,
    _serialize_toml,
    load_config,
    save_config,
    load_env,
    load_config,
)


# ─── Color pairs for curses ──────────────────────────────────────────────────

CP_HEADER = 1
CP_TITLE = 2
CP_KEY = 3
CP_VALUE = 4
CP_HIGHLIGHT = 5
CP_SELECTED = 6
CP_STATUS = 7
CP_ERROR = 8
CP_DIM = 9
CP_SECRET = 10
CP_BORDER = 11
CP_INPUT = 12
CP_WARN = 13


def _init_colors() -> None:
    """Initialize curses color pairs."""
    curses.start_color()
    curses.use_default_colors()

    #                pair    fg           bg
    curses.init_pair(CP_HEADER, curses.COLOR_CYAN, -1)
    curses.init_pair(CP_TITLE, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(CP_KEY, curses.COLOR_GREEN, -1)
    curses.init_pair(CP_VALUE, curses.COLOR_YELLOW, -1)
    curses.init_pair(CP_HIGHLIGHT, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(CP_SELECTED, curses.COLOR_BLACK, curses.COLOR_GREEN)
    curses.init_pair(CP_STATUS, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(CP_ERROR, curses.COLOR_WHITE, curses.COLOR_RED)
    curses.init_pair(CP_DIM, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(CP_SECRET, curses.COLOR_RED, -1)
    curses.init_pair(CP_BORDER, curses.COLOR_CYAN, -1)
    curses.init_pair(CP_INPUT, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(CP_WARN, curses.COLOR_YELLOW, -1)


# ─── UI Helpers ──────────────────────────────────────────────────────────────


def _draw_border(win: "curses.window", color_pair: int = CP_BORDER) -> None:
    """Draw a border around a window."""
    h, w = win.getmaxyx()
    if h < 2 or w < 2:
        return
    try:
        win.attron(curses.color_pair(color_pair))
        win.border()
        win.attroff(curses.color_pair(color_pair))
    except curses.error:
        pass


def _center_text(win: "curses.window", y: int, text: str, color_pair: int = 0) -> None:
    """Write centered text at row y."""
    h, w = win.getmaxyx()
    x = max(0, (w - len(text)) // 2)
    try:
        if color_pair:
            win.attron(curses.color_pair(color_pair))
        win.addstr(y, x, text[:w - 1])
        if color_pair:
            win.attroff(curses.color_pair(color_pair))
    except curses.error:
        pass


def _truncate(text: str, max_len: int) -> str:
    """Truncate text to max_len with ellipsis."""
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."


# ─── Input dialog ────────────────────────────────────────────────────────────


def input_dialog(stdscr: "curses.window", prompt: str, default: str = "", secret: bool = False) -> Optional[str]:
    """Show a centered input dialog. Returns the input string or None on cancel."""
    curses.curs_set(1)
    h, w = stdscr.getmaxyx()
    dialog_h = 5
    dialog_w = min(70, w - 8)
    sy = (h - dialog_h) // 2
    sx = (w - dialog_w) // 2

    win = curses.newwin(dialog_h, dialog_w, sy, sx)
    win.keypad(True)
    win.clear()

    result = list(default)
    pos = len(result)

    while True:
        win.clear()
        _draw_border(win, CP_BORDER)
        # Prompt line
        try:
            win.attron(curses.color_pair(CP_HEADER) | curses.A_BOLD)
            win.addstr(1, 2, _truncate(prompt, dialog_w - 4))
            win.attroff(curses.color_pair(CP_HEADER) | curses.A_BOLD)
        except curses.error:
            pass

        # Input field
        display = "*" * len(result) if secret else "".join(result)
        try:
            win.attron(curses.color_pair(CP_INPUT))
            win.addstr(3, 2, "> " + _truncate(display, dialog_w - 6))
            win.attroff(curses.color_pair(CP_INPUT))
        except curses.error:
            pass

        win.refresh()
        key = stdscr.getch()

        if key == 27:  # ESC
            curses.curs_set(0)
            return None
        elif key in (10, 13, curses.KEY_ENTER):  # Enter
            curses.curs_set(0)
            return "".join(result)
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            if pos > 0:
                pos -= 1
                result.pop(pos)
        elif key == curses.KEY_DC:
            if pos < len(result):
                result.pop(pos)
        elif key == curses.KEY_LEFT:
            if pos > 0:
                pos -= 1
        elif key == curses.KEY_RIGHT:
            if pos < len(result):
                pos += 1
        elif key == curses.KEY_HOME:
            pos = 0
        elif key == curses.KEY_END:
            pos = len(result)
        elif 32 <= key <= 126:
            result.insert(pos, chr(key))
            pos += 1


# ─── Confirm dialog ──────────────────────────────────────────────────────────


def confirm_dialog(stdscr: "curses.window", message: str) -> bool:
    """Show a yes/no confirmation dialog. Returns True for Yes."""
    h, w = stdscr.getmaxyx()
    lines = textwrap.wrap(message, min(60, w - 8))
    dialog_h = len(lines) + 5
    dialog_w = min(64, w - 4)
    sy = (h - dialog_h) // 2
    sx = (w - dialog_w) // 2

    win = curses.newwin(dialog_h, dialog_w, sy, sx)
    win.keypad(True)
    selected = 0  # 0 = Yes, 1 = No

    while True:
        win.clear()
        _draw_border(win, CP_BORDER)
        for i, line in enumerate(lines):
            try:
                win.addstr(1 + i, 2, _truncate(line, dialog_w - 4))
            except curses.error:
                pass

        # Buttons
        btn_y = len(lines) + 2
        btn_texts = ["[ Yes ]", "[  No ]"]
        for i, bt in enumerate(btn_texts):
            x = dialog_w // 2 - 8 + i * 12
            if i == selected:
                win.attron(curses.color_pair(CP_SELECTED) | curses.A_BOLD)
            else:
                win.attron(curses.color_pair(CP_DIM))
            try:
                win.addstr(btn_y, x, bt)
            except curses.error:
                pass
            win.attroff(curses.color_pair(CP_SELECTED) | curses.A_BOLD)
            win.attroff(curses.color_pair(CP_DIM))

        win.refresh()
        key = stdscr.getch()
        if key == curses.KEY_LEFT:
            selected = 0
        elif key == curses.KEY_RIGHT:
            selected = 1
        elif key in (10, 13, curses.KEY_ENTER):
            return selected == 0
        elif key == 27:
            return False


# ─── Notification bar ────────────────────────────────────────────────────────


def show_notification(stdscr: "curses.window", msg: str, is_error: bool = False) -> None:
    """Show a brief notification at the bottom of the screen."""
    h, w = stdscr.getmaxyx()
    try:
        color = CP_ERROR if is_error else CP_STATUS
        stdscr.attron(curses.color_pair(color) | curses.A_BOLD)
        stdscr.addstr(h - 1, 0, " " * (w - 1))
        stdscr.addstr(h - 1, 0, _truncate(msg, w - 2))
        stdscr.attroff(curses.color_pair(color) | curses.A_BOLD)
        stdscr.refresh()
        curses.napms(1500)
    except curses.error:
        pass


# ─── Main TUI ────────────────────────────────────────────────────────────────


def run_tui() -> int:
    """Launch the interactive TUI config viewer/editor."""
    try:
        return curses.wrapper(_tui_main)
    except Exception as e:
        _err(f"TUI error: {e}")
        return 1


def _tui_main(stdscr: "curses.window") -> int:
    """Main TUI loop."""
    _init_colors()
    curses.curs_set(0)
    curses.cbreak()
    stdscr.keypad(True)
    curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)

    # State
    current_file: Optional[str] = None
    config_data: Dict[str, Any] = {}
    config_keys: List[str] = []
    selected_idx = 0
    scroll_offset = 0
    status_msg = "Press F1 for help | o: open | q: quit"
    is_dirty = False
    editing_mode = False  # When True, pressing Enter edits the selected value
    filtered_keys: Optional[List[str]] = None
    search_query = ""

    def _refresh_data() -> None:
        """Refresh the config_keys list from config_data."""
        nonlocal config_keys
        if filtered_keys is not None:
            config_keys = filtered_keys
        else:
            config_keys = list(config_data.keys())

    def _load_file(path: str) -> bool:
        """Load a config file. Returns True on success."""
        nonlocal current_file, config_data, config_keys, selected_idx, scroll_offset, is_dirty, filtered_keys, search_query
        if not os.path.isfile(path):
            show_notification(stdscr, f"File not found: {path}", True)
            return False
        try:
            config_data = load_config(path)
            if not isinstance(config_data, dict):
                config_data = {}
        except Exception as e:
            show_notification(stdscr, f"Failed to load: {e}", True)
            return False
        current_file = path
        filtered_keys = None
        search_query = ""
        _refresh_data()
        selected_idx = 0
        scroll_offset = 0
        is_dirty = False
        show_notification(stdscr, f"Loaded {len(config_data)} keys from {path}")
        return True

    def _save_file() -> bool:
        """Save the current config data."""
        nonlocal is_dirty
        if current_file is None:
            show_notification(stdscr, "No file open", True)
            return False
        try:
            save_config(current_file, config_data)
            is_dirty = False
            show_notification(stdscr, f"Saved to {current_file}")
            return True
        except Exception as e:
            show_notification(stdscr, f"Save failed: {e}", True)
            return False

    def _filter_keys(query: str) -> None:
        """Set a search filter on keys."""
        nonlocal filtered_keys, config_keys, selected_idx, search_query
        search_query = query
        if not query:
            filtered_keys = None
        else:
            q = query.lower()
            filtered_keys = [k for k in config_data.keys() if q in k.lower()]
        _refresh_data()
        selected_idx = 0

    def _add_key(key: str, value: str) -> bool:
        """Add a new key-value pair. Returns True on success."""
        nonlocal is_dirty
        if not key or not key.replace("_", "").isalnum():
            show_notification(stdscr, "Invalid key name", True)
            return False
        if key in config_data:
            show_notification(stdscr, f"Key '{key}' already exists", True)
            return False
        config_data[key] = value
        _refresh_data()
        is_dirty = True
        return True

    def _delete_key(key: str) -> bool:
        """Delete a key. Returns True on success."""
        nonlocal is_dirty
        if key not in config_data:
            return False
        del config_data[key]
        _refresh_data()
        is_dirty = True
        return True

    def _edit_value(key: str) -> bool:
        """Edit a key's value via dialog. Returns True on success."""
        nonlocal is_dirty
        cur_val = str(config_data.get(key, ""))
        # Check if value looks encrypted
        is_secret = isinstance(cur_val, str) and cur_val.startswith("$CV$")
        new_val = input_dialog(stdscr, f"Value for {key}:", default=cur_val, secret=False)
        if new_val is None:
            return False  # Cancelled
        config_data[key] = new_val
        is_dirty = True
        return True

    # ── Main loop ────────────────────────────────────────────────────────

    while True:
        h, w = stdscr.getmaxyx()
        if h < 10 or w < 20:
            stdscr.clear()
            _center_text(stdscr, h // 2, "Terminal too small (min 20x10)")
            stdscr.refresh()
            stdscr.getch()
            continue

        stdscr.clear()

        # ── Header bar ────────────────────────────────────────────────
        try:
            stdscr.attron(curses.color_pair(CP_TITLE))
            title = " config-vault "
            if current_file:
                title += f"| {os.path.basename(current_file)} "
            title += f"| {len(config_data)} keys "
            if is_dirty:
                title += "| *MODIFIED* "
            stdscr.addstr(0, 0, " " * (w - 1))
            _center_text(stdscr, 0, title)
            stdscr.attroff(curses.color_pair(CP_TITLE))
        except curses.error:
            pass

        # ── Search bar (if active) ────────────────────────────────────
        if search_query:
            try:
                stdscr.attron(curses.color_pair(CP_HIGHLIGHT))
                stdscr.addstr(1, 0, " " * (w - 1))
                stdscr.addstr(1, 0, f" Search: {search_query}  ({len(config_keys)} matches)")
                stdscr.attroff(curses.color_pair(CP_HIGHLIGHT))
            except curses.error:
                pass

        # ── Key/Value list ────────────────────────────────────────────
        header_row = 1 if search_query else 1
        list_start_y = header_row + 1
        list_height = h - list_start_y - 2  # -2 for status lines

        # Column widths
        key_col_w = max(20, w // 3)
        val_col_w = w - key_col_w - 4
        if val_col_w < 10:
            val_col_w = 10
            key_col_w = w - val_col_w - 4

        # Column headers
        if list_height > 0:
            try:
                stdscr.attron(curses.color_pair(CP_DIM) | curses.A_BOLD)
                stdscr.addstr(header_row, 2, "KEY".ljust(key_col_w))
                stdscr.addstr(header_row, 3 + key_col_w, "VALUE")
                stdscr.attroff(curses.color_pair(CP_DIM) | curses.A_BOLD)
            except curses.error:
                pass

        # Ensure selected_idx is in range
        if selected_idx >= len(config_keys):
            selected_idx = max(0, len(config_keys) - 1)
        if selected_idx < 0:
            selected_idx = 0

        # Scroll logic
        if selected_idx < scroll_offset:
            scroll_offset = selected_idx
        if selected_idx >= scroll_offset + list_height:
            scroll_offset = selected_idx - list_height + 1
        if scroll_offset < 0:
            scroll_offset = 0

        # Draw items
        visible_keys = config_keys[scroll_offset:scroll_offset + list_height]

        for i, key in enumerate(visible_keys):
            y = list_start_y + i
            if y >= h - 2:
                break

            val = config_data.get(key, "")
            val_str = str(val)[:val_col_w - 1] if val is not None else ""

            # Detect secrets for highlighting
            is_secret_val = isinstance(val, str) and (
                val.startswith("$CV$") or
                any(kw in key.upper() for kw in ["PASSWORD", "SECRET", "TOKEN", "API_KEY", "APIKEY"])
            )

            is_selected = (scroll_offset + i) == selected_idx

            if is_selected:
                stdscr.attron(curses.color_pair(CP_SELECTED))
                try:
                    stdscr.addstr(y, 1, " " * (w - 2))
                except curses.error:
                    pass
            else:
                stdscr.attron(curses.color_pair(CP_KEY))

            # Draw key
            try:
                key_display = _truncate(key, key_col_w)
                stdscr.addstr(y, 2, key_display.ljust(key_col_w))
            except curses.error:
                pass

            # Draw value
            val_color = CP_SECRET if is_secret_val else CP_VALUE
            try:
                val_display = _truncate(val_str, val_col_w)
                if is_selected:
                    stdscr.attron(curses.color_pair(CP_SELECTED))
                else:
                    stdscr.attron(curses.color_pair(val_color))
                stdscr.addstr(y, 3 + key_col_w, val_display.ljust(val_col_w))
            except curses.error:
                pass

            if is_selected:
                stdscr.attroff(curses.color_pair(CP_SELECTED))
            else:
                stdscr.attroff(curses.color_pair(CP_KEY))
                stdscr.attroff(curses.color_pair(val_color))

        # ── Scroll indicator ────────────────────────────────────────────
        if len(config_keys) > list_height:
            scroll_pct = scroll_offset / max(1, len(config_keys) - list_height)
            scroll_bar_pos = int(scroll_pct * (list_height - 2))
            try:
                stdscr.attron(curses.color_pair(CP_DIM))
                stdscr.addstr(list_start_y + scroll_bar_pos, 0, "█")
                stdscr.attroff(curses.color_pair(CP_DIM))
            except curses.error:
                pass

        # ── Status bar ──────────────────────────────────────────────────
        try:
            stdscr.attron(curses.color_pair(CP_STATUS))
            stdscr.addstr(h - 2, 0, " " * (w - 1))
            stdscr.addstr(h - 2, 0, _truncate(status_msg, w - 2))
            stdscr.attroff(curses.color_pair(CP_STATUS))
        except curses.error:
            pass

        # ── Help bar ────────────────────────────────────────────────────
        help_text = (
            "F1:Help  o:Open  s:Save  /:Search  a:Add  d:Delete  e:Edit  "
            "r:Reload  ESC:Cancel  q:Quit"
        )
        try:
            stdscr.attron(curses.color_pair(CP_DIM))
            stdscr.addstr(h - 1, 0, " " * (w - 1))
            stdscr.addstr(h - 1, 0, _truncate(help_text, w - 2))
            stdscr.attroff(curses.color_pair(CP_DIM))
        except curses.error:
            pass

        stdscr.refresh()

        # ── Handle Input ──────────────────────────────────────────────
        key = stdscr.getch()

        if key == ord("q"):
            if is_dirty:
                if confirm_dialog(stdscr, "Unsaved changes. Quit anyway?"):
                    break
            else:
                break

        elif key == ord("o"):
            fpath = input_dialog(stdscr, "Open file path:", default=current_file or ".env")
            if fpath and fpath.strip():
                _load_file(fpath.strip())

        elif key == ord("s"):
            _save_file()

        elif key == ord("a"):
            k = input_dialog(stdscr, "New key name:")
            if k and k.strip():
                v = input_dialog(stdscr, f"Value for '{k.strip()}':")
                if v is not None:
                    _add_key(k.strip(), v if v else "")
                    status_msg = f"Added key: {k.strip()}"

        elif key == ord("d"):
            if config_keys and 0 <= selected_idx < len(config_keys):
                key_to_del = config_keys[selected_idx]
                if confirm_dialog(stdscr, f"Delete '{key_to_del}'?"):
                    _delete_key(key_to_del)
                    status_msg = f"Deleted key: {key_to_del}"

        elif key == ord("e"):
            if config_keys and 0 <= selected_idx < len(config_keys):
                key_to_edit = config_keys[selected_idx]
                if _edit_value(key_to_edit):
                    status_msg = f"Edited: {key_to_edit}"

        elif key == ord("/"):
            q = input_dialog(stdscr, "Search keys:", default=search_query)
            if q is not None:
                _filter_keys(q)
                if search_query:
                    status_msg = f"Searching: {search_query} ({len(config_keys)} matches)"
                else:
                    status_msg = "Search cleared"

        elif key == ord("r"):
            if current_file:
                if is_dirty:
                    if confirm_dialog(stdscr, "Reload file? Unsaved changes will be lost."):
                        _load_file(current_file)
                else:
                    _load_file(current_file)
                status_msg = f"Reloaded: {current_file}"

        elif key == ord("n"):
            # Toggle editing mode
            editing_mode = not editing_mode
            if editing_mode:
                status_msg = "Edit mode ON (Enter to edit selected value)"
            else:
                status_msg = "Edit mode OFF"

        elif key == curses.KEY_UP:
            if selected_idx > 0:
                selected_idx -= 1

        elif key == curses.KEY_DOWN:
            if selected_idx < len(config_keys) - 1:
                selected_idx += 1

        elif key == curses.KEY_PPAGE:  # Page Up
            selected_idx = max(0, selected_idx - list_height)

        elif key == curses.KEY_NPAGE:  # Page Down
            selected_idx = min(len(config_keys) - 1, selected_idx + list_height)

        elif key == curses.KEY_HOME:
            selected_idx = 0

        elif key == curses.KEY_END:
            selected_idx = len(config_keys) - 1

        elif key == curses.KEY_ENTER or key in (10, 13):
            if editing_mode and config_keys and 0 <= selected_idx < len(config_keys):
                key_to_edit = config_keys[selected_idx]
                if _edit_value(key_to_edit):
                    status_msg = f"Edited: {key_to_edit}"

        elif key == curses.KEY_F1 or key == ord("?"):
            _show_help(stdscr)

        elif key == ord("c"):
            # Copy selected value to clipboard notification
            if config_keys and 0 <= selected_idx < len(config_keys):
                val = config_data.get(config_keys[selected_idx], "")
                status_msg = f"Value copied for '{config_keys[selected_idx]}' (length: {len(str(val))})"

        elif key == 27:  # ESC
            if search_query:
                _filter_keys("")
                status_msg = "Search cleared"
            elif is_dirty:
                if confirm_dialog(stdscr, "Unsaved changes. Quit anyway?"):
                    break
            else:
                # Error beep
                curses.beep()
                status_msg = "Press q to quit"

    return 0


# ─── Help Screen ──────────────────────────────────────────────────────────────


def _show_help(stdscr: "curses.window") -> None:
    """Display the help screen overlay."""
    h, w = stdscr.getmaxyx()
    help_h = min(24, h - 4)
    help_w = min(60, w - 4)
    sy = (h - help_h) // 2
    sx = (w - help_w) // 2

    win = curses.newwin(help_h, help_w, sy, sx)
    win.keypad(True)

    help_lines = [
        ("config-vault TUI Help", True),
        ("", False),
        ("Navigation:", True),
        ("  ↑/↓        : Move selection", False),
        ("  PgUp/PgDn  : Page scroll", False),
        ("  Home/End   : Jump to start/end", False),
        ("", False),
        ("Actions:", True),
        ("  o          : Open a config file", False),
        ("  s          : Save changes", False),
        ("  e          : Edit selected value", False),
        ("  a          : Add new key", False),
        ("  d          : Delete selected key", False),
        ("  /          : Search/filter keys", False),
        ("  r          : Reload current file", False),
        ("  n          : Toggle edit-on-enter mode", False),
        ("", False),
        ("Formats supported:", True),
        ("  .env  .json  .yaml/.yml  .toml", False),
        ("", False),
        ("  ESC : Cancel / Clear search", False),
        ("  q   : Quit", False),
        ("", False),
        ("Press any key to close this help.", False),
    ]

    while True:
        win.clear()
        win.attron(curses.color_pair(CP_BORDER))
        win.box()
        win.attroff(curses.color_pair(CP_BORDER))

        for i, (line, is_header) in enumerate(help_lines):
            if i + 1 >= help_h - 1:
                break
            try:
                if is_header:
                    win.attron(curses.A_BOLD | curses.color_pair(CP_HEADER))
                    win.addstr(i + 1, 2, _truncate(line, help_w - 4))
                    win.attroff(curses.A_BOLD | curses.color_pair(CP_HEADER))
                else:
                    win.addstr(i + 1, 2, _truncate(line, help_w - 4))
            except curses.error:
                pass

        win.refresh()
        k = stdscr.getch()
        if k in (10, 13, curses.KEY_ENTER, 27, ord("q"), ord("?"), curses.KEY_F1):
            break


# ─── Standalone entry point ──────────────────────────────────────────────────


def main() -> int:
    """TUI entry point when run directly."""
    return run_tui()


if __name__ == "__main__":
    sys.exit(main())
