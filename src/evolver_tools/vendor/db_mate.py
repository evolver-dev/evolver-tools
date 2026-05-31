"""db-mate — Database manager (CLI+TUI). Integrated from evolver-packages."""
TOOL_META = {"name": "db-mate", "desc": "Database management: SQLite browser, schema, queries — CLI+TUI", "func": "entry"}

try:
    from db_mate.cli import entry
except ImportError:
    import sys
    sys.path.insert(0, "/root/evolver-packages/db-mate/src")
    from db_mate.cli import entry
