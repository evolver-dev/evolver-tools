"""log-hawk — Log analysis toolkit (CLI+TUI). Integrated from evolver-packages."""
TOOL_META = {"name": "log-hawk", "desc": "Log analysis: parse, filter, tail, stats — CLI+TUI", "func": "main"}

try:
    from log_hawk.cli import main
except ImportError:
    import sys
    sys.path.insert(0, "/root/evolver-packages/log-hawk/src")
    from log_hawk.cli import main
