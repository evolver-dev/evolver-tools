"""Interactive TUI browser for SQLite databases using curses."""

import curses
import sqlite3
import os
import textwrap
from .cli import (
    _find_dbs,
    _connect,
    _get_table_info,
    _quote,
    _human_size,
    green,
    cyan,
    yellow,
    red,
    bold,
    dim,
)


def _strip_ansi(s):
    """Remove ANSI escape sequences for curses rendering."""
    import re
    return re.sub(r"\033\[[0-9;]*m", "", s)


def run_tui(db_path=None):
    """Launch the curses-based TUI."""
    # Pick a database if not provided
    if db_path is None:
        dbs = _find_dbs()
        if not dbs:
            print(red("No .db files found. Specify one with --db <path>"))
            return
        if len(dbs) == 1:
            db_path = dbs[0]
        else:
            db_path = _tui_pick_db(dbs)

    curses.wrapper(_main_loop, db_path)


def _tui_pick_db(dbs):
    """Simple terminal picker for multiple databases."""
    print(cyan("Multiple databases found:"))
    for i, d in enumerate(dbs, 1):
        sz = os.path.getsize(d)
        print(f"  {i}. {d}  ({_human_size(sz)})")
    while True:
        try:
            c = input("Enter number: ").strip()
            return dbs[int(c) - 1]
        except (ValueError, IndexError):
            print(red("Invalid choice."))


def _main_loop(stdscr, db_path):
    curses.curs_set(0)
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, -1)    # table names
    curses.init_pair(2, curses.COLOR_CYAN, -1)     # column names
    curses.init_pair(3, curses.COLOR_YELLOW, -1)   # highlights
    curses.init_pair(4, curses.COLOR_MAGENTA, -1)  # PK
    curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLUE)  # selected row
    curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_WHITE)  # header

    conn = _connect(db_path)
    info = _get_table_info(conn)

    state = {
        "conn": conn,
        "db_path": db_path,
        "info": info,
        "mode": "tables",      # tables | browse | sql
        "table_idx": 0,
        "scroll": 0,
        "browse_offset": 0,    # column scroll offset for data view
        "sql_input": "",
        "sql_result": [],
        "sql_cols": [],
        "sql_scroll": 0,
        "status": f"db: {os.path.basename(db_path)}",
    }

    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()

        if state["mode"] == "tables":
            _draw_tables(stdscr, state, h, w)
        elif state["mode"] == "browse":
            _draw_browse(stdscr, state, h, w)
        elif state["mode"] == "sql":
            _draw_sql(stdscr, state, h, w)

        stdscr.refresh()
        key = stdscr.getch()

        if key == ord("q"):
            break
        elif key == ord("t"):
            state["mode"] = "tables"
            state["scroll"] = 0
        elif key == ord("b"):
            if state["info"]:
                state["mode"] = "browse"
                state["browse_offset"] = 0
                state["scroll"] = 0
        elif key == ord("s"):
            state["mode"] = "sql"
            state["sql_input"] = ""
            state["sql_result"] = []
            state["sql_cols"] = []
            state["sql_scroll"] = 0
        elif key == ord("j") or key == curses.KEY_DOWN:
            state["scroll"] += 1
        elif key == ord("k") or key == curses.KEY_UP:
            state["scroll"] = max(0, state["scroll"] - 1)
        elif key == ord("n"):
            if state["mode"] == "tables" and state["info"]:
                state["table_idx"] = (state["table_idx"] + 1) % len(state["info"])
        elif key == ord("p"):
            if state["mode"] == "tables" and state["info"]:
                state["table_idx"] = (state["table_idx"] - 1) % len(state["info"])
        elif key == ord("h") or key == curses.KEY_LEFT:
            if state["mode"] == "browse":
                state["browse_offset"] = max(0, state["browse_offset"] - 3)
        elif key == ord("l") or key == curses.KEY_RIGHT:
            if state["mode"] == "browse":
                state["browse_offset"] += 3
        elif key == 10:  # Enter — execute SQL or select table
            if state["mode"] == "sql":
                _exec_sql(state)

    conn.close()


def _draw_tables(stdscr, state, h, w):
    """Draw the tables overview screen."""
    info = state["info"]
    scroll = state["scroll"]
    sel_idx = state["table_idx"]

    # Header
    header = f" db-mate TUI — {os.path.basename(state['db_path'])} "
    stdscr.attron(curses.color_pair(6))
    stdscr.addstr(0, 0, header.center(w, " "))
    stdscr.attroff(curses.color_pair(6))

    # Key bindings
    help_line = " [t]ables  [b]rowse table  [s]ql  [n]ext  [p]rev  [j/k]scroll  [Enter]detail  [q]uit "
    stdscr.attron(curses.A_DIM)
    stdscr.addstr(h - 1, 0, help_line[:w])
    stdscr.attroff(curses.A_DIM)

    line = 2
    if not info:
        stdscr.addstr(line, 2, "No tables found.", curses.A_DIM)
        return

    for idx, t in enumerate(info):
        if line >= h - 2:
            break

        name = t["name"]
        row_s = str(t["row_count"])
        col_s = str(len(t["columns"]))
        prefix = "▸" if idx == sel_idx else " "

        if idx == sel_idx:
            stdscr.attron(curses.color_pair(5))
            stdscr.addstr(line, 2, f" {prefix} {name} ".ljust(w - 4))
            stdscr.attroff(curses.color_pair(5))
        else:
            stdscr.attron(curses.color_pair(1))
            stdscr.addstr(line, 2, f" {prefix} {name}")
            stdscr.attroff(curses.color_pair(1))

        stdscr.attron(curses.A_DIM)
        stdscr.addstr(line, w - 20, f"{row_s:>6} rows  {col_s} cols")
        stdscr.attroff(curses.A_DIM)
        line += 1

    # If a table is selected, show its columns
    if info and sel_idx < len(info):
        t = info[sel_idx]
        line += 1
        if line < h - 2:
            stdscr.attron(curses.A_UNDERLINE)
            stdscr.addstr(line, 4, f"Columns of {t['name']}:")
            stdscr.attroff(curses.A_UNDERLINE)
            line += 1

            for col in t["columns"]:
                if line >= h - 2:
                    break
                cname = col["name"]
                ctype = col["type"] or "?"
                pk = " PK" if col["pk"] else ""
                nn = " NOT NULL" if col["notnull"] else ""
                stdscr.attron(curses.color_pair(2))
                stdscr.addstr(line, 6, f"  {cname}")
                stdscr.attroff(curses.color_pair(2))
                stdscr.attron(curses.A_DIM)
                stdscr.addstr(f"  {ctype}{pk}{nn}")
                stdscr.attroff(curses.A_DIM)
                line += 1


def _draw_browse(stdscr, state, h, w):
    """Browse data rows of a selected table."""
    conn = state["conn"]
    info = state["info"]
    if not info:
        return
    t = info[state["table_idx"]]
    tname = t["name"]
    scroll = state["scroll"]

    # Fetch data
    try:
        rows = conn.execute(f"SELECT * FROM {_quote(tname)} LIMIT 500").fetchall()
    except sqlite3.Error:
        rows = []
    cols = [d[0] for d in conn.execute(
        f"SELECT * FROM {_quote(tname)} LIMIT 0"
    ).description] if rows else [c["name"] for c in t["columns"]]

    if not cols:
        return

    # Header
    stdscr.attron(curses.color_pair(6))
    header = f" {tname}  ({len(rows)} rows)  [←/→ scroll columns] "
    stdscr.addstr(0, 0, header.center(w, " "))
    stdscr.attroff(curses.color_pair(6))

    # Help
    help_line = " [t]ables  [b]rowse  [s]ql  [j/k]scroll  [←/→]cols  [q]uit "
    stdscr.attron(curses.A_DIM)
    stdscr.addstr(h - 1, 0, help_line[:w])
    stdscr.attroff(curses.A_DIM)

    boff = state["browse_offset"]
    visible_cols = cols[boff:boff + 6]
    if not visible_cols:
        visible_cols = cols[-6:]
        boff = max(0, len(cols) - 6)

    # Calculate widths
    col_widths = []
    for i, c in enumerate(visible_cols):
        actual_idx = boff + i
        maxw = max(len(str(c)), 4)
        for r in rows:
            val = str(r[actual_idx]) if r[actual_idx] is not None else "NULL"
            maxw = max(maxw, len(val))
        col_widths.append(min(maxw + 2, 30))

    # Draw column headers
    line = 2
    x = 2
    stdscr.attron(curses.A_BOLD)
    for i, c in enumerate(visible_cols):
        ww = col_widths[i]
        name = c[:ww - 1] if len(c) >= ww else c
        stdscr.addstr(line, x, f" {name}".ljust(ww))
        x += ww
    stdscr.attroff(curses.A_BOLD)
    line += 1

    # Draw separator
    x = 2
    for ww in col_widths:
        stdscr.addstr(line, x, "─" * ww, curses.A_DIM)
        x += ww
    line += 1

    # Draw rows
    start_row = scroll
    for idx in range(start_row, min(start_row + h - line - 2, len(rows))):
        r = rows[idx]
        x = 2
        for i, c in enumerate(visible_cols):
            actual_idx = boff + i
            ww = col_widths[i]
            val = str(r[actual_idx]) if r[actual_idx] is not None else "NULL"
            if len(val) > ww - 1:
                val = val[:ww - 4] + "..."
            stdscr.addstr(line, x, f" {val}".ljust(ww))
            x += ww
        line += 1

        if line >= h - 2:
            break

    # Scroll indicator
    if len(rows) > h - 5:
        pct = int((scroll / max(1, len(rows) - (h - 5))) * 100)
        stdscr.addstr(h - 2, w - 10, dim(f"  {pct}%  "))


def _draw_sql(stdscr, state, h, w):
    """SQL query input and result display."""
    # Header
    stdscr.attron(curses.color_pair(6))
    header = " SQL Query  [Enter] execute "
    stdscr.addstr(0, 0, header.center(w, " "))
    stdscr.attroff(curses.color_pair(6))

    # Input area
    stdscr.addstr(2, 2, "SQL> ")
    input_x = 7
    input_w = w - input_x - 2
    display = state["sql_input"][-(input_w - 1):] if len(state["sql_input"]) > input_w else state["sql_input"]
    stdscr.addstr(2, input_x, display.ljust(input_w))
    stdscr.addstr(2, input_x + len(display), " ")

    # Help
    help_line = " [t]ables  [b]rowse  [s]ql  [j/k]scroll  [q]uit "
    stdscr.attron(curses.A_DIM)
    stdscr.addstr(h - 1, 0, help_line[:w])
    stdscr.attroff(curses.A_DIM)

    # Results
    if state["sql_result"]:
        cols = state["sql_cols"]
        scroll = state["sql_scroll"]
        rows = state["sql_result"]

        # Column widths
        col_widths = []
        for i, c in enumerate(cols):
            maxw = len(str(c))
            for r in rows:
                val = str(r[i]) if r[i] is not None else "NULL"
                maxw = max(maxw, len(val))
            col_widths.append(min(maxw + 2, 30))

        line = 4
        x = 2
        stdscr.attron(curses.A_BOLD)
        for i, c in enumerate(cols[:8]):
            ww = col_widths[i]
            name = c[:ww - 1] if len(c) >= ww else c
            stdscr.addstr(line, x, f" {name}".ljust(ww))
            x += ww
        stdscr.attroff(curses.A_BOLD)
        line += 1

        x = 2
        for i in range(min(8, len(col_widths))):
            stdscr.addstr(line, x, "─" * col_widths[i], curses.A_DIM)
            x += col_widths[i]
        line += 1

        for idx in range(scroll, min(scroll + h - line - 2, len(rows))):
            r = rows[idx]
            x = 2
            for i in range(min(8, len(cols))):
                ww = col_widths[i]
                val = str(r[i]) if r[i] is not None else "NULL"
                if len(val) > ww - 1:
                    val = val[:ww - 4] + "..."
                stdscr.addstr(line, x, f" {val}".ljust(ww))
                x += ww
            line += 1
            if line >= h - 2:
                break

        stdscr.attron(curses.A_DIM)
        stdscr.addstr(h - 2, 2, f"{len(rows)} row(s)")
        stdscr.attroff(curses.A_DIM)
    else:
        stdscr.addstr(4, 2, "Type a SQL query above and press Enter.", curses.A_DIM)


def _exec_sql(state):
    """Execute the SQL input and store results."""
    sql = state["sql_input"].strip()
    if not sql:
        return
    try:
        cur = state["conn"].execute(sql)
        state["sql_result"] = cur.fetchall()
        state["sql_cols"] = [d[0] for d in cur.description] if cur.description else []
        state["sql_scroll"] = 0
    except sqlite3.Error as e:
        state["sql_result"] = []
        state["sql_cols"] = ["ERROR"]
        state["sql_result"] = [(str(e),)]
