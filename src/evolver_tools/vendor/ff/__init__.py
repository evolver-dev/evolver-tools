"""ff: Interactive fuzzy finder — pure Python, zero dependencies.

Read items from stdin or file, then interactively search and select.
Heavily inspired by fzf (junegunn/fzf). Uses curses for the TUI.

Usage:
  cat file.txt | ff                # Pipe mode
  ff -f file.txt                   # File mode
  find . -type f | ff              # Pipe from find
  ps aux | ff                      # Pipe process list
  ff -m < file.txt                 # Multi-select mode
"""

import sys
import os
import curses
import textwrap

__version__ = "1.0.0"


# ─── Fuzzy matching ───────────────────────────────────────────────────────────

def fuzzy_match(query: str, text: str) -> bool:
    """Simple subsequence matching: does query appear in order in text?"""
    query = query.lower()
    text_lower = text.lower()
    qi = 0
    for ch in text_lower:
        if qi < len(query) and ch == query[qi]:
            qi += 1
    return qi == len(query)


def score_match(query: str, text: str) -> int:
    """Score a fuzzy match — higher is better.

    Bonuses for:
    - Consecutive match (adjacent chars in query match adjacent in text)
    - Match at word boundary
    - Match at start of line
    - Match starting at capital letter
    """
    query = query.lower()
    text_lower = text.lower()
    score = 0
    qi = 0
    prev_was_boundary = True  # Start-of-line is a boundary

    for ti, ch in enumerate(text_lower):
        if qi < len(query) and ch == query[qi]:
            if qi == 0:
                # First character match
                if ti == 0:
                    score += 50  # Start of line
                elif prev_was_boundary:
                    score += 40  # After word boundary
                else:
                    score += 10  # General match
            else:
                if prev_was_boundary:
                    score += 30  # Consecutive + boundary
                else:
                    # Check if previous char in text matches previous char in query
                    if qi > 0 and ti > 0 and text_lower[ti - 1] == query[qi - 1]:
                        score += 20  # Consecutive match
                    else:
                        score += 5  # Non-consecutive
            qi += 1

        # Track word boundaries
        prev = text_lower[ti] if ti < len(text_lower) else ''
        prev_was_boundary = ch in (' ', '-', '_', '/', '.', ':', '(', '[') or (
            ch.isupper() and ti > 0 and text[ti - 1].islower()
        )

    return score


def highlight_matches(query: str, text: str) -> list:
    """Return list of (char, is_match) tuples for display."""
    if not query:
        return [(c, False) for c in text]

    query_lower = query.lower()
    text_lower = text.lower()
    qi = 0
    result = []
    for ch in text:
        if qi < len(query_lower) and ch.lower() == query_lower[qi]:
            result.append((ch, True))
            qi += 1
        else:
            result.append((ch, False))
    return result


# ─── Curses UI ────────────────────────────────────────────────────────────────

def run_fzf(items: list, multi: bool = False, preview: str = None) -> list:
    """Run the interactive fuzzy finder and return selected items."""
    if not items:
        return []

    selected = []
    current_idx = 0
    query = ""

    def get_matches():
        if not query:
            return list(enumerate(items))
        scored = []
        for i, item in enumerate(items):
            if fuzzy_match(query, item):
                sc = score_match(query, item)
                scored.append((sc, i, item))
        scored.sort(key=lambda x: (-x[0], x[1]))
        return [(i, item) for _, i, item in scored]

    def draw(stdscr):
        nonlocal current_idx
        curses.curs_set(1)
        curses.use_default_colors()
        max_y, max_x = stdscr.getmaxyx()

        # Color pairs
        curses.init_pair(1, curses.COLOR_CYAN, -1)    # Query text
        curses.init_pair(2, curses.COLOR_GREEN, -1)   # Selected items
        curses.init_pair(3, curses.COLOR_YELLOW, -1)  # Match highlights
        curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLUE)  # Cursor line
        curses.init_pair(5, curses.COLOR_RED, -1)     # Count / status

        matches = get_matches()

        # Clamp selection
        if current_idx >= len(matches):
            current_idx = max(0, len(matches) - 1)

        # Input line
        prompt = "> " if not multi else "> [multi] "
        stdscr.attron(curses.color_pair(1) | curses.A_BOLD)
        stdscr.addstr(0, 0, prompt)
        stdscr.attroff(curses.color_pair(1) | curses.A_BOLD)

        query_display = query
        if len(query_display) > max_x - len(prompt) - 1:
            query_display = query_display[-(max_x - len(prompt) - 1):]
        stdscr.addstr(0, len(prompt), query_display)
        cursor_x = len(prompt) + len(query_display)

        # Status line
        status = f" {len(matches)}/{len(items)}"
        if multi:
            sel_count = len(selected)
            status += f" | {sel_count} selected"

        stdscr.attron(curses.A_REVERSE)
        try:
            if len(status) < max_x:
                stdscr.addstr(1, 0, status.ljust(max_x - 1))
        except curses.error:
            pass
        stdscr.attroff(curses.A_REVERSE)

        # Results area
        visible_height = max_y - 2
        scroll_offset = 0
        if current_idx >= visible_height:
            scroll_offset = current_idx - visible_height + 1

        for i in range(visible_height):
            idx = scroll_offset + i
            if idx >= len(matches):
                break

            match_idx, item = matches[idx]
            is_cursor = idx == current_idx

            # Truncate item
            display_item = item.replace('\t', ' ' * 4).replace('\n', ' ')
            if len(display_item) > max_x - 2:
                display_item = display_item[:max_x - 5] + '...'

            is_selected = match_idx in selected

            if is_cursor:
                stdscr.attron(curses.color_pair(4))
                sel_marker = ">" if is_selected else " "
                line = f"{sel_marker} {display_item}".ljust(max_x - 1)
                try:
                    stdscr.addstr(i + 2, 0, line[:max_x - 1])
                except curses.error:
                    pass
                stdscr.attroff(curses.color_pair(4))
            elif is_selected:
                stdscr.attron(curses.color_pair(2))
                try:
                    stdscr.addstr(i + 2, 0, f"* {display_item}"[:max_x - 1])
                except curses.error:
                    pass
                stdscr.attroff(curses.color_pair(2))
            else:
                try:
                    stdscr.addstr(i + 2, 0, f"  {display_item}"[:max_x - 1])
                except curses.error:
                    pass

        # Clear rest of screen
        for i in range(len(matches) - scroll_offset, visible_height):
            try:
                stdscr.addstr(i + 2, 0, " " * (max_x - 1))
            except curses.error:
                pass

        return cursor_x

    # ─── Main input loop ──────────────────────────────────────────────────

    selected_result = []
    done = False

    def main(stdscr):
        nonlocal current_idx, query, selected_result, done

        curses.cbreak()
        curses.noecho()
        stdscr.keypad(True)

        while not done:
            cursor_x = draw(stdscr)
            stdscr.move(1, 0)  # Move cursor to status line field (safe zone)
            stdscr.refresh()

            try:
                key = stdscr.get_wch()
            except KeyboardInterrupt:
                selected_result = None
                break

            if isinstance(key, str):
                if key == '\n':  # Enter
                    matches = [item for _, item in (
                        (i, item) for i, item in enumerate(items) if fuzzy_match(query, item)
                    ) if True]
                    if multi:
                        if selected:
                            selected_result = selected.copy()
                        elif matches:
                            idx = current_idx if current_idx < len(matches) else 0
                            selected_result = [matches[idx] if idx < len(matches) else '']
                    else:
                        matches_list = [
                            item for _, item in (list(enumerate(items)) if not query else
                                [(i, items[i]) for i, _ in [(i, item) for i, item in enumerate(items) if fuzzy_match(query, item)]]
                            )
                        ]
                        # Re-get matches correctly
                        scored = []
                        for i, item in enumerate(items):
                            if fuzzy_match(query, item):
                                sc = score_match(query, item)
                                scored.append((sc, i, item))
                        scored.sort(key=lambda x: (-x[0], x[1]))
                        matches_list = [item for _, _, item in scored]
                        if matches_list:
                            idx = min(current_idx, len(matches_list) - 1)
                            selected_result = [matches_list[idx]]
                    done = True
                    return

                elif key == '\x1b':  # Escape
                    selected_result = None
                    done = True
                    return

                elif key == '\t' and multi:  # Tab to select/deselect
                    matches = [
                        item for _, item in (
                            [(i, items[i]) for i, item in enumerate(items) if fuzzy_match(query, item)]
                        )
                    ]
                    if matches:
                        idx = min(current_idx, len(matches) - 1)
                        match_orig_idx = items.index(matches[idx])  # inefficient but works
                        # Find the original index
                        orig_idx = -1
                        count = 0
                        for i, item in enumerate(items):
                            if fuzzy_match(query, item):
                                if count == current_idx:
                                    orig_idx = i
                                    break
                                count += 1
                        if orig_idx >= 0:
                            if orig_idx in selected:
                                selected.remove(orig_idx)
                            else:
                                selected.append(orig_idx)

                elif key == '\x7f':  # Backspace
                    query = query[:-1]
                    current_idx = 0

                elif key == '\x15':  # Ctrl+U — clear query
                    query = ""
                    current_idx = 0

                elif key == '\x0c':  # Ctrl+L — redraw
                    pass

                elif key.isprintable():
                    if len(query) < 200:  # Cap query length
                        query += key
                        current_idx = 0

            elif isinstance(key, int):
                if key == curses.KEY_UP:
                    if current_idx > 0:
                        current_idx -= 1
                elif key == curses.KEY_DOWN:
                    matches = sum(1 for _ in items if fuzzy_match(query, items[_] if isinstance(items, list) else items))
                    # simpler: just count matches
                    match_count = len([i for i in items if fuzzy_match(query, i)])
                    if current_idx < match_count - 1:
                        current_idx += 1
                elif key == curses.KEY_NPAGE:  # Page Down
                    match_count = len([i for i in items if fuzzy_match(query, i)])
                    current_idx = min(current_idx + 10, max(0, match_count - 1))
                elif key == curses.KEY_PPAGE:  # Page Up
                    current_idx = max(0, current_idx - 10)
                elif key == curses.KEY_HOME:
                    current_idx = 0
                elif key == curses.KEY_END:
                    match_count = len([i for i in items if fuzzy_match(query, i)])
                    current_idx = max(0, match_count - 1)
                elif key == curses.KEY_RESIZE:
                    pass

    curses.wrapper(main)

    if selected_result is None:
        return []
    return selected_result


# ─── Preview support ──────────────────────────────────────────────────────────

def preview_item(item: str, preview_cmd: str) -> str:
    """Run preview command on an item and return output."""
    import subprocess
    try:
        cmd = preview_cmd.replace('{}', item)
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=2)
        return result.stdout[:500]  # Limit preview size
    except Exception as e:
        return f"Preview error: {e}"


# ─── Main CLI ─────────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="ff — Interactive fuzzy finder (zero dependencies)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\\
Examples:
  cat file.txt | ff                    # Search through file lines
  ff -f /etc/passwd                    # Search from file
  find . -type f | ff                  # Search file listing
  ps aux | ff                          # Search process list
  ff -m < tags.txt                     # Multi-select
  ff --header "Pick a file:" < files   # Custom header
        """),
    )
    parser.add_argument("-f", "--file", help="Read items from file instead of stdin")
    parser.add_argument("-m", "--multi", action="store_true", help="Multi-select mode (Tab to toggle)")
    parser.add_argument("-q", "--query", default="", help="Start with initial query")
    parser.add_argument("--header", default="", help="Header message")
    parser.add_argument("--version", action="store_true", help="Show version")
    args = parser.parse_args()

    if args.version:
        print(f"ff {__version__}")
        return

    # Read items
    items = []
    if args.file:
        try:
            with open(args.file) as f:
                items = [line.rstrip('\n\r') for line in f]
        except FileNotFoundError:
            print(f"ff: {args.file}: No such file", file=sys.stderr)
            sys.exit(1)
        except PermissionError:
            print(f"ff: {args.file}: Permission denied", file=sys.stderr)
            sys.exit(1)
    else:
        if sys.stdin.isatty():
            print("ff: No input. Pipe data to stdin or use -f FILE.", file=sys.stderr)
            sys.exit(1)
        items = [line.rstrip('\n\r') for line in sys.stdin]

    if not items:
        sys.exit(1)

    # Remove trailing empty lines
    while items and items[-1] == '':
        items.pop()

    # Apply initial query
    query = args.query

    # Run the finder
    result = run_fzf(items, multi=args.multi)

    if result:
        for item in result:
            print(item)
    else:
        sys.exit(1)



# === Auto-registration metadata ===
TOOL_META = {
    "name": "ff",
    "func": "main",
    "desc": 'Fuzzy Finder',
}

if __name__ == "__main__":
    main()
