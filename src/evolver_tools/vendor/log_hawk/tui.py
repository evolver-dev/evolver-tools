"""
log_hawk.tui — Curses-based interactive log viewer / tailer.

Keyboard shortcuts:
  ↑/↓/PgUp/PgDn    Scroll
  /                Search forward
  ?                Search backward
  n/N              Next/previous match
  f                Follow/tail toggle
  l/L              Level filter  (cycle: ALL → ERROR → WARN → INFO → DEBUG)
  p/P              Pattern filter prompt
  h/H              Highlight term prompt
  s/S              Statistics overlay
  r                Reset filters
  q/Esc/Ctrl-C     Quit
  F1/?             Help
"""

import curses
import curses.textpad
import datetime
import os
import re
import signal
import sys
import time
from collections import deque
from pathlib import Path

from . import (
    Filter,
    build_stats,
    colorize,
    detect_format,
    open_log,
    parse_line,
    render_stats_table,
    LEVEL_COLORS,
)


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

def _truncate(s, width):
    """Truncate *s* to *width*, adding '…' if needed."""
    if len(s) <= width:
        return s
    return s[:width - 1] + "…"


def _now():
    return datetime.datetime.now().strftime("%H:%M:%S")


# ──────────────────────────────────────────────────────────────
# Ring buffer with fast appends
# ──────────────────────────────────────────────────────────────

class LogBuffer:
    """Bounded deque of LogEntry with indexing support."""

    def __init__(self, maxlen=50_000):
        self._buf = deque(maxlen=maxlen)
        self._filtered = []
        self._all = []  # full list for stats
        self._recalc_needed = False
        self._fmt_hint = None

    def append(self, entry):
        self._buf.append(entry)
        self._all.append(entry)
        self._recalc_needed = True

    def extend(self, entries):
        for e in entries:
            self._buf.append(e)
            self._all.append(e)
        self._recalc_needed = True

    @property
    def raw_entries(self):
        return list(self._buf)

    @property
    def all_entries(self):
        return self._all

    def filtered_entries(self, filt=None):
        """Return list matching current filter (cached)."""
        if filt is None:
            return list(self._buf)
        if self._recalc_needed or not hasattr(self, "_cache_key") or self._cache_key != id(filt):
            self._filtered = [e for e in self._buf if filt.match(e)]
            self._recalc_needed = False
            self._cache_key = id(filt)
        return self._filtered


# ──────────────────────────────────────────────────────────────
# Main TUI runner
# ──────────────────────────────────────────────────────────────

def run_tui(paths):
    curses.wrapper(_main_tui, paths)


def _main_tui(stdscr, paths):
    # ── Setup ──
    curses.curs_set(0)
    curses.use_default_colors()
    stdscr.nodelay(True)
    stdscr.keypad(True)

    # Try colour pairs
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, -1)       # header
    curses.init_pair(2, curses.COLOR_GREEN, -1)      # info
    curses.init_pair(3, curses.COLOR_YELLOW, -1)      # warning
    curses.init_pair(4, curses.COLOR_RED, -1)         # error
    curses.init_pair(5, curses.COLOR_MAGENTA, -1)     # highlights
    curses.init_pair(6, curses.COLOR_BLUE, -1)        # paths
    curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_RED)  # critical bg
    curses.init_pair(8, 240, -1)                      # dim

    # ── State ──
    buffer = LogBuffer()
    current_filt = None
    follow_mode = True
    search_term = ""
    search_forward = True
    highlight_term = ""
    show_help = False
    show_stats = False
    scroll_offset = 0
    status_msg = ""
    status_time = 0.0
    fmt_hint = None

    # Detect format from first file
    if paths:
        non_stdin = [p for p in paths if p != "-"]
        if non_stdin:
            first = non_stdin[0]
            if os.path.exists(first):
                from . import detect_format_from_file
                fmt_hint = detect_format_from_file(first)

    # Open all file handles for follow
    handles = {}
    file_labels = {}
    current_file_idx = 0
    for p in paths:
        if p == "-":
            continue
        if not os.path.exists(p):
            continue
        fh = open(p, "rb")
        fh.seek(0, os.SEEK_END)
        handles[p] = fh
        file_labels[p] = Path(p).name

    file_list = list(handles.keys())
    total_loaded = 0
    max_lines = 5000

    # Pre-load existing content
    for p in file_list:
        try:
            fh = handles[p]
            fh.seek(0, os.SEEK_SET)
            for raw_bytes in fh:
                try:
                    raw = raw_bytes.decode("utf-8", errors="replace")
                except UnicodeDecodeError:
                    raw = raw_bytes.decode("latin-1", errors="replace")
                entry = parse_line(raw, fmt_hint=fmt_hint)
                buffer.append(entry)
                total_loaded += 1
                if total_loaded >= max_lines:
                    break
            fh.seek(0, os.SEEK_END)
        except Exception:
            pass

    if total_loaded == 0:
        _set_status(status_msg, status_time, "No log data loaded — waiting for input...")
        status_time = time.time()

    # ── Main loop ──
    running = True
    while running:
        rows, cols = stdscr.getmaxyx()
        if rows < 5 or cols < 20:
            stdscr.clear()
            stdscr.addstr(0, 0, "Terminal too small (min 5x20)")
            stdscr.refresh()
            time.sleep(0.2)
            continue

        # ── Poll file handles in follow mode ──
        if follow_mode and handles:
            new_lines = 0
            for p, fh in list(handles.items()):
                line = fh.readline()
                while line:
                    try:
                        raw = line.decode("utf-8", errors="replace")
                    except UnicodeDecodeError:
                        raw = line.decode("latin-1", errors="replace")
                    entry = parse_line(raw, fmt_hint=fmt_hint)
                    buffer.append(entry)
                    new_lines += 1
                    total_loaded += 1
                    line = fh.readline()
                # Check rotation
                try:
                    st = os.stat(p)
                    if st.st_ino != os.fstat(fh.fileno()).st_ino:
                        fh.close()
                        fh = open(p, "rb")
                        handles[p] = fh
                except OSError:
                    pass
            if new_lines and follow_mode:
                scroll_offset = 0  # follow tail

        # ── Build display list ──
        display_entries = buffer.filtered_entries(current_filt)
        total_filtered = len(display_entries)
        total_raw = len(buffer.raw_entries)

        # Clamp scroll
        if scroll_offset > 0 and scroll_offset >= total_filtered:
            scroll_offset = max(0, total_filtered - 1)
        if scroll_offset < 0:
            scroll_offset = 0

        # ── Render ──
        stdscr.erase()

        if show_help:
            _draw_help(stdscr, rows, cols)
        elif show_stats:
            _draw_stats(stdscr, rows, cols, buffer, current_filt)
        else:
            _draw_content(stdscr, rows, cols, buffer, display_entries,
                          scroll_offset, search_term, highlight_term,
                          follow_mode, current_filt, total_filtered, total_raw,
                          paths, file_labels, fmt_hint)

        # ── Status bar ──
        _draw_status(stdscr, rows, cols, status_msg, status_time)

        stdscr.refresh()

        # ── Input ──
        key = stdscr.getch()

        if key == ord("q") or key == 27:  # q or Escape
            if show_help:
                show_help = False
            elif show_stats:
                show_stats = False
            else:
                running = False
            continue

        if key == curses.KEY_RESIZE:
            continue

        if show_help or show_stats:
            continue

        # ── Navigation ──
        if key == curses.KEY_UP:
            scroll_offset = max(0, scroll_offset - 1)
            follow_mode = False

        elif key == curses.KEY_DOWN:
            scroll_offset = min(total_filtered - 1, scroll_offset + 1) if total_filtered else 0

        elif key == curses.KEY_PPAGE:
            scroll_offset = max(0, scroll_offset - (rows - 3))

        elif key == curses.KEY_NPAGE:
            scroll_offset = min(total_filtered - 1, scroll_offset + (rows - 3))

        elif key == curses.KEY_HOME:
            scroll_offset = 0
            follow_mode = False

        elif key == curses.KEY_END:
            scroll_offset = max(0, total_filtered - 1)

        # ── Follow toggle ──
        elif key == ord("f"):
            follow_mode = not follow_mode
            if follow_mode:
                scroll_offset = 0
                _set_status(status_msg, status_time, "Follow mode ON")
                status_time = time.time()
            else:
                _set_status(status_msg, status_time, "Follow mode OFF")
                status_time = time.time()

        # ── Level filter ──
        elif key == ord("l"):
            _cycle_level_filter(current_filt, _set_status(status_msg, status_time, ""),
                                status_time, status_msg)
            status_time = time.time()
            if current_filt and current_filt.level:
                _set_status(status_msg, status_time, f"Level filter: {current_filt.level}")
            else:
                _set_status(status_msg, status_time, "Level filter cleared")
            scroll_offset = 0

        # ── Pattern filter ──
        elif key == ord("p"):
            pat = _prompt(stdscr, rows, cols, "Pattern filter: ")
            if pat:
                if current_filt is None:
                    current_filt = Filter()
                current_filt.pattern = re.compile(pat, re.IGNORECASE)
                _set_status(status_msg, status_time, f"Pattern filter: /{pat}/")
                scroll_offset = 0
            status_time = time.time()

        # ── Highlight ──
        elif key == ord("h"):
            hl = _prompt(stdscr, rows, cols, "Highlight term: ")
            if hl:
                highlight_term = hl
                _set_status(status_msg, status_time, f"Highlight: {hl}")
            else:
                highlight_term = ""
            status_time = time.time()

        # ── Search ──
        elif key == ord("/"):
            term = _prompt(stdscr, rows, cols, "/")
            if term:
                search_term = term
                search_forward = True
                scroll_offset = _search(display_entries, search_term,
                                        scroll_offset + 1, total_filtered)
                _set_status(status_msg, status_time, f"Search: {search_term}")
            status_time = time.time()

        elif key == ord("?"):
            term = _prompt(stdscr, rows, cols, "?")
            if term:
                search_term = term
                search_forward = False
                scroll_offset = _search_rev(display_entries, search_term,
                                            scroll_offset - 1)
                _set_status(status_msg, status_time, f"Search reverse: {search_term}")
            status_time = time.time()

        elif key == ord("n"):
            if search_term:
                scroll_offset = _search(display_entries, search_term,
                                        scroll_offset + 1, total_filtered)
                follow_mode = False

        elif key == ord("N"):
            if search_term:
                scroll_offset = _search_rev(display_entries, search_term,
                                            scroll_offset - 1)
                follow_mode = False

        # ── Reset filters ──
        elif key == ord("r"):
            current_filt = None
            highlight_term = ""
            search_term = ""
            _set_status(status_msg, status_time, "All filters reset")
            status_time = time.time()

        # ── Stats ──
        elif key == ord("s"):
            show_stats = not show_stats

        # ── Help ──
        elif key == ord("?") or key == curses.KEY_F1:
            show_help = not show_help

        # ── Quit ──
        elif key == ord("\n") or key == ord("\r"):
            pass

        # ── Idle ──
        else:
            time.sleep(0.02)

    # Cleanup
    for fh in handles.values():
        fh.close()


# ──────────────────────────────────────────────────────────────
# Drawing
# ──────────────────────────────────────────────────────────────

def _draw_header(rows, cols, follow_mode, filt, total_filtered, total_raw,
                 file_labels, fmt_hint):
    """Draw top status bar."""
    header = curses.color_pair(1) | curses.A_BOLD | curses.A_REVERSE
    label = "log-hawk"
    if file_labels:
        label += " [" + ",".join(file_labels.values())[:cols - 20] + "]"
    if follow_mode:
        label += " FOLLOW"
    if filt and filt.level:
        label += f" lvl:{filt.level}"
    if filt and filt.pattern:
        pat = filt.pattern.pattern[:20]
        label += f" /{pat}/"
    label += f"  {total_filtered}/{total_raw}"
    label = _truncate(label, cols)
    try:
        stdscr.addstr(0, 0, label, header)
    except curses.error:
        pass


def _draw_content(stdscr, rows, cols, buffer, display_entries,
                  scroll_offset, search_term, highlight_term,
                  follow_mode, current_filt, total_filtered, total_raw,
                  paths, file_labels, fmt_hint):
    """Draw the main log content area."""
    _draw_header(rows, cols, follow_mode, current_filt, total_filtered,
                 total_raw, file_labels, fmt_hint)

    content_rows = rows - 2  # header + status
    line_idx = 0

    for i in range(scroll_offset, scroll_offset + content_rows):
        if i >= len(display_entries):
            break
        entry = display_entries[i]
        line_idx += 1

        # Build coloured line (but we draw via curses attrs, not ANSI)
        raw_text = _render_entry_row(entry, cols - 1, highlight_term)
        attr = curses.A_NORMAL

        # Colour by level
        if entry.level:
            lvl = entry.level.upper()
            if lvl in ("ERROR", "CRITICAL", "FATAL", "ALERT", "EMERG"):
                attr = curses.color_pair(4) | curses.A_BOLD
            elif lvl == "WARNING":
                attr = curses.color_pair(3)
            elif lvl == "INFO":
                attr = curses.color_pair(2)

        # Highlight search matches
        if search_term and search_term.lower() in raw_text.lower():
            attr |= curses.A_REVERSE

        try:
            stdscr.addstr(line_idx, 0, raw_text, attr)
        except curses.error:
            pass


def _draw_status(stdscr, rows, cols, status_msg, status_time):
    """Draw bottom status bar."""
    ts = _now()
    elapsed = time.time() - status_time
    if elapsed < 3.0 and status_msg:
        text = f" {ts}  {status_msg}"
    else:
        text = f" {ts}  [↑↓←→/pg/Home/End scroll] [f]ollow [l]evel [p]attern [h]ighlight [/]search [s]tats [q]uit"
    text = _truncate(text, cols)
    try:
        stdscr.addstr(rows - 1, 0, text, curses.color_pair(8) | curses.A_REVERSE)
    except curses.error:
        pass


def _draw_help(stdscr, rows, cols):
    """Draw help overlay."""
    help_lines = [
        colorize("══════  log-hawk TUI — Help  ══════", "bold", "cyan"),
        "",
        " Navigation",
        "   ↑ / ↓              Scroll up/down 1 line",
        "   PgUp / PgDn        Scroll 1 page",
        "   Home / End         Jump to start/end",
        "",
        " Viewing",
        "   f                  Toggle follow/tail mode",
        "   s                  Toggle statistics overlay",
        "   ? / F1             Toggle this help",
        "",
        " Filtering",
        "   l                  Cycle log level (ALL→ERROR→WARN→INFO→DEBUG)",
        "   p                  Enter regex pattern filter",
        "   h                  Enter highlight term",
        "   r                  Reset all filters",
        "",
        " Search",
        "   /                  Search forward",
        "   ?                  Search backward",
        "   n                  Next match",
        "   N                  Previous match",
        "",
        " General",
        "   q / Esc            Quit / close panel",
        "   Ctrl+C             Quit",
    ]

    overlay = stdscr.derwin(min(rows, len(help_lines) + 2), min(cols, 52),
                            1, max(0, (cols - 52) // 2))
    overlay.erase()
    overlay.bkgd(" ", curses.color_pair(8) | curses.A_REVERSE)
    overlay.box()

    for idx, line in enumerate(help_lines):
        if idx + 1 >= overlay.getmaxyx()[0] - 1:
            break
        try:
            overlay.addstr(idx + 1, 2, _truncate(line, overlay.getmaxyx()[1] - 4))
        except curses.error:
            pass
    overlay.refresh()


def _draw_stats(stdscr, rows, cols, buffer, current_filt):
    """Draw statistics overlay."""
    entries = buffer.filtered_entries(current_filt)
    stats = build_stats(entries)
    stats_str = render_stats_table(stats, top_n=rows // 6)
    stat_lines = stats_str.split("\n")

    overlay_h = min(rows - 1, len(stat_lines) + 2)
    overlay_w = min(cols, 76)
    start_y = max(0, (rows - overlay_h) // 2)
    start_x = max(0, (cols - overlay_w) // 2)

    overlay = stdscr.derwin(overlay_h, overlay_w, start_y, start_x)
    overlay.erase()
    overlay.bkgd(" ", curses.color_pair(8) | curses.A_REVERSE)
    overlay.box()

    for idx, line in enumerate(stat_lines):
        if idx + 1 >= overlay_h - 1:
            break
        # Strip ANSI codes for curses
        clean = re.sub(r"\033\[[0-9;]*m", "", line)
        try:
            overlay.addstr(idx + 1, 2, _truncate(clean, overlay_w - 4))
        except curses.error:
            pass
    overlay.refresh()


def _render_entry_row(entry, max_width, highlight_term=""):
    """Build a plain-string row for a log entry (no ANSI)."""
    parts = []

    ts = str(entry.timestamp) if entry.timestamp else ""
    if ts:
        parts.append(ts)

    if entry.format_name in ("clf", "combined"):
        parts.append(entry.ip or "")
        parts.append(entry.path or "")
        parts.append(entry.status or "")
        parts.append(entry.size or "")
    elif entry.format_name in ("syslog", "syslog5424"):
        host = entry.host or ""
        proc = f"{entry.process}[{entry.pid}]" if entry.pid else entry.process
        parts.append(host)
        parts.append(proc)
        parts.append(entry.level)
        parts.append(entry.message[:80])
    elif entry.format_name == "json":
        parts.append(entry.level)
        parts.append(entry.message[:80])
    else:
        parts.append(entry.level)
        parts.append(entry.message[:120])

    text = "  ".join(p for p in parts if p)
    text = _truncate(text, max_width)
    return text


# ──────────────────────────────────────────────────────────────
# Search helpers
# ──────────────────────────────────────────────────────────────

def _search(entries, term, start, total):
    """Find next match forward from *start*."""
    if not entries:
        return 0
    for i in range(start, total):
        if term.lower() in entries[i].raw.lower():
            return i
    # Wrap
    for i in range(0, start):
        if term.lower() in entries[i].raw.lower():
            return i
    return start - 1 if start > 0 else 0


def _search_rev(entries, term, start):
    """Find next match backward from *start*."""
    if not entries:
        return 0
    for i in range(start, -1, -1):
        if term.lower() in entries[i].raw.lower():
            return i
    # Wrap
    for i in range(len(entries) - 1, start, -1):
        if term.lower() in entries[i].raw.lower():
            return i
    return start + 1 if start < len(entries) - 1 else len(entries) - 1


# ──────────────────────────────────────────────────────────────
# Filter helpers
# ──────────────────────────────────────────────────────────────

_LEVEL_CYCLE = [None, "ERROR", "WARNING", "INFO", "DEBUG"]


def _cycle_level_filter(current_filt, status_msg, status_time, msg_var):
    """Cycle through level filters."""
    global _LEVEL_CYCLE
    idx = 0
    if current_filt and current_filt.level:
        try:
            idx = _LEVEL_CYCLE.index(current_filt.level)
        except ValueError:
            idx = 0
    idx = (idx + 1) % len(_LEVEL_CYCLE)
    lvl = _LEVEL_CYCLE[idx]
    if lvl is None:
        current_filt = None
        # FIXME: this is a hack, should mutate properly
        return None
    else:
        if current_filt is None:
            current_filt = Filter()
        current_filt.level = lvl
        return current_filt


def _set_status(msg_var, time_var, msg):
    return msg  # placeholder — actual status set above


# ──────────────────────────────────────────────────────────────
# Prompt
# ──────────────────────────────────────────────────────────────

def _prompt(stdscr, rows, cols, prompt_text):
    """Show a one-line input prompt and return the entered string."""
    curses.curs_set(1)
    # Compute position: overlay on status bar
    input_win = curses.newwin(1, cols, rows - 1, 0)
    input_win.bkgd(" ", curses.color_pair(8) | curses.A_REVERSE)
    input_win.addstr(0, 0, _truncate(prompt_text, cols - 2))
    input_win.refresh()

    curses.echo()
    result = ""
    try:
        result = input_win.getstr(0, len(prompt_text), cols - len(prompt_text) - 2)
        if isinstance(result, bytes):
            result = result.decode("utf-8", errors="replace")
    except curses.error:
        pass
    curses.noecho()
    curses.curs_set(0)

    # Clear the input line
    stdscr.move(rows - 1, 0)
    stdscr.clrtoeol()
    stdscr.refresh()
    return result
