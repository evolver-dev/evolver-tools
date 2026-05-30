"""db-mate — SQLite Database CLI Manager."""
__version__ = "1.0.0"

from .cli import entry

TOOL_META = {
    "name": "db-mate",
    "desc": "Database management: SQLite, schema, queries, TUI browser — CLI+TUI",
    "func": "entry",
}
