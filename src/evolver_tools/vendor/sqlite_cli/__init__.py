"""sqlite-cli: Zero-dependency SQLite query tool (pure Python stdlib).

A user-friendly SQLite CLI that works without installing sqlite3 separately.
Python's sqlite3 module is always available (stdlib since Python 2.5).
"""

import sys
import os
import json
import textwrap
import sqlite3
from pathlib import Path


__version__ = "1.0.0"


def detect_columns(cursor):
    """Get column names and types from cursor description."""
    if cursor.description:
        return [desc[0] for desc in cursor.description]
    return []


def format_table(rows, headers, fmt="table"):
    """Format query results in various modes."""
    if not rows and not headers:
        return "(no results)"

    if fmt == "json":
        if not headers:
            return json.dumps(rows, ensure_ascii=False) if rows else "[]"
        result = [dict(zip(headers, row)) for row in rows]
        return json.dumps(result, ensure_ascii=False, indent=2)

    if fmt == "csv":
        output = ",".join(headers) if headers else ""
        for row in rows:
            output += "\n" + ",".join(
                str(v) if v is not None else "NULL"
                for v in row
            )
        return output

    if fmt == "line":
        lines = []
        for i, row in enumerate(rows):
            if headers:
                lines.append(f"  row {i+1}:")
                for h, v in zip(headers, row):
                    lines.append(f"    {h} = {v}")
            else:
                lines.append(f"  row {i+1}: {row}")
            lines.append("")
        return "\n".join(lines).rstrip()

    if fmt == "tabs":
        output = "\t".join(headers) if headers else ""
        for row in rows:
            output += "\n" + "\t".join(
                str(v) if v is not None else "NULL"
                for v in row
            )
        return output

    # Default: table format
    if not headers:
        lines = [str(row) for row in rows]
        return "\n".join(lines)

    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, v in enumerate(row):
            if i < len(col_widths):
                s = str(v) if v is not None else "NULL"
                col_widths[i] = max(col_widths[i], len(s))

    # Cap widths at 80 for readability
    max_width = 80
    total = sum(col_widths) + 3 * len(col_widths) - 1
    if total > 120:
        for i in range(len(col_widths)):
            col_widths[i] = min(col_widths[i], max_width)

    # Build separator
    sep = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"

    def fmt_row(vals):
        parts = []
        for i, val in enumerate(vals):
            s = str(val) if val is not None else "NULL"
            if i < len(col_widths):
                w = col_widths[i]
                if len(s) > w:
                    s = s[:w - 3] + "..."
                parts.append(f" {s:<{w}} ")
            else:
                parts.append(f" {s} ")
        return "|" + "|".join(parts) + "|"

    lines = [sep, fmt_row(headers), sep]
    for row in rows:
        lines.append(fmt_row(row))
    lines.append(sep)
    lines.append(f"({len(rows)} rows)")

    return "\n".join(lines)


def run_dot_command(cursor, cmd: str, db_path: str):
    """Handle SQLite dot commands."""
    cmd = cmd.strip().lower()

    if cmd == ".tables":
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [r[0] for r in cursor.fetchall()]
        if tables:
            # Print in columns
            cols = 4
            for i in range(0, len(tables), cols):
                print("  ".join(tables[i:i+cols]))
        else:
            print("(no tables)")
        return True

    if cmd == ".schema":
        cursor.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL")
        schemas = [r[0] for r in cursor.fetchall()]
        for s in schemas:
            print(s + ";")
            print()
        if not schemas:
            print("(no schema)")
        return True

    if cmd == ".databases":
        print(f"  {db_path or ':memory:'}")
        return True

    if cmd == ".indexes":
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' ORDER BY name")
        indexes = [r[0] for r in cursor.fetchall()]
        if indexes:
            print("\n".join(indexes))
        else:
            print("(no indexes)")
        return True

    if cmd.startswith(".schema "):
        table = cmd[8:].strip()
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=? AND sql IS NOT NULL", (table,))
        row = cursor.fetchone()
        if row:
            print(row[0] + ";")
        else:
            print(f"Error: no such table: {table}", file=sys.stderr)
        return True

    if cmd.startswith(".mode "):
        # This is handled before execution, not here
        return True

    if cmd == ".help":
        print("""Dot commands:
  .tables                  List all tables
  .schema [table]          Show CREATE statement(s)
  .indexes                 List all indexes
  .databases               Show connected database
  .mode MODE               Set output mode (table|csv|json|line|tabs|column)
  .exit                    Quit
  .help                    Show this help""")
        return True

    return False


def exec_query(cursor, sql: str, mode: str = "table"):
    """Execute a SQL query and print results."""
    sql = sql.strip().rstrip(";")
    if not sql:
        return

    try:
        cursor.execute(sql)
    except sqlite3.Error as e:
        print(f"Error: {e}", file=sys.stderr)
        return

    # For SELECT-like queries, fetch and display results
    if sql.upper().lstrip().startswith(("SELECT", "PRAGMA", "EXPLAIN")):
        rows = cursor.fetchall()
        headers = detect_columns(cursor)
        output = format_table(rows, headers, fmt=mode)
        if output:
            print(output)
    else:
        # DML/DDL: show affected rows
        print(f"({cursor.rowcount} rows affected)" if cursor.rowcount >= 0 else "OK")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="sqlite-cli — Zero-dependency SQLite query tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sqlite-cli db.sqlite3 "SELECT * FROM users"
  sqlite-cli db.sqlite3 --mode json "SELECT id, name FROM users"
  echo "SELECT count(*) FROM users" | sqlite-cli db.sqlite3
  sqlite-cli --init schema.sql db.sqlite3
  sqlite-cli --tables db.sqlite3
  sqlite-cli db.sqlite3 ".tables"
  sqlite-cli db.sqlite3 ".schema users"
  sqlite-cli --schema users db.sqlite3
  sqlite-cli --schema-all db.sqlite3
        """
    )
    parser.add_argument("database", help="Path to SQLite database file")
    parser.add_argument("query", nargs="*", help="SQL query or dot command")
    parser.add_argument("--mode", "-m", default="table", choices=["table", "csv", "json", "line", "tabs", "column"],
                        help="Output format (default: table)")
    parser.add_argument("--init", "-i", help="SQL file to execute before query (e.g., CREATE TABLE)")
    parser.add_argument("--tables", action="store_true", help="List all tables (shortcut)")
    parser.add_argument("--schema", nargs=1, metavar="TABLE", default=None,
                        help="Show schema for a specific table (omit for all)")
    parser.add_argument("--schema-all", action="store_true",
                        help="Show schema for all tables")

    args = parser.parse_intermixed_args()

    # Resolve DB path
    db_path = args.database

    # Handle .sqlite or .db shortcuts
    if not os.path.exists(db_path) and not db_path == ":memory:":
        print(f"Warning: database not found: {db_path}", file=sys.stderr)
        print("Creating new database...", file=sys.stderr)

    # Connect
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA journal_mode=WAL")
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}", file=sys.stderr)
        sys.exit(1)

    cursor = conn.cursor()

    # Run init file if provided
    if args.init:
        try:
            with open(args.init) as f:
                init_sql = f.read()
            cursor.executescript(init_sql)
            conn.commit()
            print(f"Executed init script: {args.init}", file=sys.stderr)
        except FileNotFoundError:
            print(f"Error: init file not found: {args.init}", file=sys.stderr)
            sys.exit(1)
        except sqlite3.Error as e:
            print(f"Error executing init script: {e}", file=sys.stderr)
            sys.exit(1)

    # Handle --tables shortcut
    if args.tables:
        run_dot_command(cursor, ".tables", db_path)
        conn.close()
        return

    # Handle --schema shortcut
    if args.schema is not None:
        run_dot_command(cursor, f".schema {args.schema[0]}", db_path)
        conn.close()
        return

    # Handle --schema-all
    if args.schema_all:
        run_dot_command(cursor, ".schema", db_path)
        conn.close()
        return

    # Get query
    if args.query:
        query_text = " ".join(args.query)
    elif args.init:
        # init only - no query needed
        conn.close()
        return
    else:
        # Read from stdin (non-interactive only)
        stdin_data = sys.stdin.read()
        if stdin_data and stdin_data.strip():
            query_text = stdin_data.strip()
        else:
            print("Error: no query provided (provide as argument or pipe from stdin)", file=sys.stderr)
            print("Usage: sqlite-cli database.sqlite3 'SELECT * FROM table'", file=sys.stderr)
            conn.close()
            sys.exit(1)

    # Handle dot commands
    if query_text.startswith("."):
        if query_text.startswith(".mode "):
            mode = query_text[6:].strip()
            print(f"  Mode set to: {mode}")
        elif not run_dot_command(cursor, query_text, db_path):
            print(f"Unknown dot command: {query_text.split()[0]}", file=sys.stderr)
            sys.exit(1)
        conn.close()
        return

    # Execute SQL query
    try:
        exec_query(cursor, query_text, mode=args.mode)
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()



# === Auto-registration metadata ===
TOOL_META = {
    "name": "sqlite-cli",
    "func": "main",
    "desc": 'Sqlite CLI',
}

if __name__ == "__main__":
    main()
