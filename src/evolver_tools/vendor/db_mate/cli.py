"""db-mate CLI — color-coded SQLite database manager."""

import sqlite3
import csv
import json
import os
import sys
import shutil
import textwrap

# ── ANSI color helpers ───────────────────────────────────────────────────────

def _c(code, text):
    return f"\033[{code}m{text}\033[0m"

def green(text):   return _c("32", text)
def cyan(text):    return _c("36", text)
def yellow(text):  return _c("33", text)
def red(text):     return _c("31", text)
def blue(text):    return _c("34", text)
def magenta(text): return _c("35", text)
def bold(text):    return _c("1", text)
def dim(text):     return _c("2", text)
def uline(text):   return _c("4", text)

# ── DB discovery ─────────────────────────────────────────────────────────────

def _find_dbs():
    dbs = [f for f in os.listdir(".") if f.endswith(".db") or f.endswith(".sqlite") or f.endswith(".sqlite3")]
    return sorted(dbs)


def _pick_db(db_path=None):
    if db_path:
        if not os.path.isfile(db_path):
            print(red(f"Error: database file not found — {db_path}"))
            sys.exit(1)
        return db_path
    dbs = _find_dbs()
    if not dbs:
        print(red("No .db / .sqlite files found in current directory."))
        print("  Specify one with:  db-mate --db <path> <command>")
        sys.exit(1)
    if len(dbs) == 1:
        return dbs[0]
    print(cyan("Multiple databases found — pick one:"))
    for i, d in enumerate(dbs, 1):
        sz = os.path.getsize(d)
        print(f"  {bold(str(i) + '.')} {d}  ({_human_size(sz)})")
    try:
        choice = input("Enter number: ").strip()
        return dbs[int(choice) - 1]
    except (ValueError, IndexError):
        print(red("Invalid choice."))
        sys.exit(1)


def _human_size(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def _connect(db_path):
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(red(f"Error connecting to database: {e}"))
        sys.exit(1)


def _get_table_info(conn):
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    result = []
    for (tname,) in tables:
        cols = conn.execute(f"PRAGMA table_info({_quote(tname)})").fetchall()
        try:
            row_count = conn.execute(f"SELECT COUNT(*) FROM {_quote(tname)}").fetchone()[0]
        except sqlite3.Error:
            row_count = -1
        result.append({"name": tname, "columns": cols, "row_count": row_count})
    return result


def _quote(name):
    return f'"{name}"'


# ── Commands ─────────────────────────────────────────────────────────────────

def cmd_list(args, db_path):
    """List all tables with their column names and types (compact)."""
    conn = _connect(db_path)
    info = _get_table_info(conn)
    if not info:
        print(yellow("No tables found in database."))
        return
    print(bold(uline("Tables")))
    print()
    for t in info:
        print(f"  {green(t['name'])}  ({dim(str(t['row_count']) + ' rows')})")
        for col in t["columns"]:
            pk = " PK" if col["pk"] else ""
            nullable = "" if col["notnull"] else "?"
            print(f"    {cyan(col['name'])}  {dim(col['type'])}{pk}{nullable}")
        print()
    conn.close()


def cmd_schema(args, db_path):
    """Show full schema as an ASCII diagram."""
    conn = _connect(db_path)
    tables = []
    for (tname,) in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall():
        cols = conn.execute(f"PRAGMA table_info({_quote(tname)})").fetchall()
        ddl_rows = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
            (tname,),
        ).fetchall()
        ddl = (ddl_rows[0][0] or "") if ddl_rows else ""
        tables.append({"name": tname, "columns": cols, "ddl": ddl})

    term_w = shutil.get_terminal_size((80, 24)).columns
    box_w = min(term_w - 4, 72)

    for t in tables:
        header = f"  {t['name']}  "
        sep = "─" * (box_w - 2)
        print(f"  ┌{sep}┐")
        print(f"  │{header.center(box_w - 2)}{'│' if (box_w - 2) > len(header) else '│'}")
        print(f"  ├{'─' * (box_w - 2)}┤")
        for col in t["columns"]:
            name = col["name"]
            ctype = col["type"] or ""
            pk = "  🔑" if col["pk"] else ""
            nn = "  NOT NULL" if col["notnull"] else ""
            dflt = f"  DEFAULT {col['dflt_value']}" if col["dflt_value"] else ""
            line = f" {cyan(name)}  {dim(ctype)}{green(pk)}{yellow(nn)}{dim(dflt)}"
            # truncate if too long
            if len(line) > box_w - 4:
                line = line[: box_w - 7] + "..."
            print(f"  │ {line.ljust(box_w - 4)} │")
        print(f"  └{'─' * (box_w - 2)}┘")
        if t["ddl"]:
            print(f"  {dim(t['ddl'][:term_w - 4])}")
        print()

    conn.close()


def cmd_tables(args, db_path):
    """List tables with row counts and column details."""
    conn = _connect(db_path)
    info = _get_table_info(conn)
    if not info:
        print(yellow("No tables found."))
        return

    term_w = shutil.get_terminal_size((80, 24)).columns
    name_w = max(len(t["name"]) for t in info) + 2
    print(f"{bold('Table').ljust(name_w)}  {bold('Rows')}  {bold('Columns')}")
    print("─" * (name_w + 20))
    for t in info:
        col_summary = ", ".join(
            f"{c['name']}:{c['type'] or '?'}" for c in t["columns"]
        )
        max_col_w = term_w - name_w - 12
        col_display = col_summary[:max_col_w] if max_col_w > 0 else col_summary[:40]
        print(f"  {green(t['name']).ljust(name_w)}  {str(t['row_count']).rjust(5)}  {dim(col_display)}")
    conn.close()


def cmd_query(args, db_path):
    """Run an arbitrary SQL query and show results in a table."""
    if not args:
        print(red("Error: missing SQL query."))
        print("  Usage: db-mate query \"SELECT * FROM table\"")
        sys.exit(1)
    sql = " ".join(args)
    conn = _connect(db_path)
    try:
        cur = conn.execute(sql)
    except sqlite3.Error as e:
        print(red(f"SQL error: {e}"))
        sys.exit(1)

    rows = cur.fetchall()
    if not rows:
        print(yellow("Query returned no rows."))
        conn.close()
        return

    cols = [d[0] for d in cur.description]
    term_w = shutil.get_terminal_size((80, 24)).columns

    # Column widths
    col_widths = []
    for i, c in enumerate(cols):
        maxw = len(str(c))
        for r in rows:
            val = str(r[i]) if r[i] is not None else "NULL"
            maxw = max(maxw, len(val))
        col_widths.append(min(maxw + 2, term_w // max(len(cols), 1)))

    # Header
    hdr = "│"
    for i, c in enumerate(cols):
        w = col_widths[i]
        hdr += f" {bold(c).center(w - 1)}│"
    top = "┌" + "┬".join("─" * w for w in col_widths) + "┐"
    mid = "├" + "┼".join("─" * w for w in col_widths) + "┤"
    bot = "└" + "┴".join("─" * w for w in col_widths) + "┘"

    print(top)
    print(hdr)
    print(mid)

    for r in rows:
        line = "│"
        for i, val in enumerate(r):
            w = col_widths[i]
            s = str(val) if val is not None else dim("NULL")
            # Truncate if necessary
            if len(s) > w - 1:
                s = s[: w - 4] + "..."
            line += f" {s.ljust(w - 1)}│"
        print(line)
    print(bot)
    print(dim(f"  {len(rows)} row(s) returned"))
    conn.close()


def cmd_export(args, db_path):
    """Export a table as CSV or JSON."""
    if len(args) < 2:
        print(red("Usage: db-mate export <table> <csv|json> [output-file]"))
        sys.exit(1)
    table = args[0]
    fmt = args[1].lower()
    outfile = args[2] if len(args) > 2 else None

    conn = _connect(db_path)
    try:
        rows = conn.execute(f"SELECT * FROM {_quote(table)}").fetchall()
    except sqlite3.Error as e:
        print(red(f"Error: {e}"))
        sys.exit(1)
    cols = [d[0] for d in conn.execute(f"SELECT * FROM {_quote(table)} LIMIT 0").description]

    if not outfile:
        outfile = f"{table}.{fmt}"

    if fmt == "csv":
        with open(outfile, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(cols)
            for r in rows:
                w.writerow([r[c] for c in cols])
        print(green(f"Exported {len(rows)} rows to {outfile}"))

    elif fmt == "json":
        data = [{c: r[c] for c in cols} for r in rows]
        with open(outfile, "w") as f:
            json.dump(data, f, indent=2, default=str)
        print(green(f"Exported {len(rows)} rows to {outfile}"))

    else:
        print(red(f"Unsupported format: {fmt} (use csv or json)"))
        sys.exit(1)
    conn.close()


def cmd_import(args, db_path):
    """Import a CSV file into a table."""
    if len(args) < 2:
        print(red("Usage: db-mate import <table> <csv-file>"))
        sys.exit(1)
    table = args[0]
    csvfile = args[1]

    if not os.path.isfile(csvfile):
        print(red(f"File not found: {csvfile}"))
        sys.exit(1)

    conn = _connect(db_path)
    with open(csvfile, newline="") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if not header:
            print(red("CSV file is empty."))
            sys.exit(1)

        # Build insert statement
        cols = ",".join(_quote(h) for h in header)
        placeholders = ",".join("?" for _ in header)
        insert_sql = f"INSERT INTO {_quote(table)} ({cols}) VALUES ({placeholders})"

        count = 0
        try:
            for row in reader:
                conn.execute(insert_sql, row)
                count += 1
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            print(red(f"Import error (row {count + 1}): {e}"))
            sys.exit(1)

    print(green(f"Imported {count} rows into {table}"))
    conn.close()


def cmd_stats(args, db_path):
    """Show database statistics."""
    conn = _connect(db_path)
    info = _get_table_info(conn)

    sz = os.path.getsize(db_path)
    print(bold(uline(f"Database: {db_path}")))
    print(f"  Size:  {bold(_human_size(sz))}")
    print(f"  Tables: {bold(str(len(info)))}")
    total_rows = 0
    print()
    print(bold("  Table breakdown:"))
    for t in info:
        total_rows += max(0, t["row_count"])
        col_types = {}
        for c in t["columns"]:
            ct = c["type"] or "?"
            col_types[ct] = col_types.get(ct, 0) + 1
        type_str = ", ".join(f"{k}×{v}" for k, v in sorted(col_types.items()))
        print(f"    {green(t['name']).ljust(24)} {str(t['row_count']).rjust(6)} rows  {dim(type_str)}")
    print()
    print(f"  Total rows across all tables: {bold(str(total_rows))}")

    # Index info
    indexes = conn.execute(
        "SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL ORDER BY name"
    ).fetchall()
    if indexes:
        print(f"  Indexes: {bold(str(len(indexes)))}")
        for idx, tbl in indexes:
            print(f"    {cyan(idx)}  →  {tbl}")
    conn.close()


def print_help():
    print(__import__("db_mate").__doc__)


def entry(args=None, db_path=None):
    """Dispatch CLI commands. Called from __main__ or directly."""
    if args is None:
        args = sys.argv[1:]

    if not args or args[0] in ("--help", "-h"):
        print_help()
        return

    # Extract --db <path> from args
    extra_args = []
    i = 0
    while i < len(args):
        if args[i] == "--db" and i + 1 < len(args):
            db_path = args[i + 1]
            i += 2
        else:
            extra_args.append(args[i])
            i += 1
    args = extra_args

    # Auto-detect db if not provided
    if db_path is None:
        db_path = _pick_db()

    command_map = {
        "list": cmd_list,
        "schema": cmd_schema,
        "tables": cmd_tables,
        "query": cmd_query,
        "export": cmd_export,
        "import": cmd_import,
        "stats": cmd_stats,
    }

    cmd = args[0]
    if cmd in command_map:
        command_map[cmd](args[1:], db_path)
    else:
        print(red(f"Unknown command: {cmd}"))
        print_help()
        sys.exit(1)
