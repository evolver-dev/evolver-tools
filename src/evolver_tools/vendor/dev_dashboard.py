"""dev-dashboard — Developer dashboard (CLI+TUI). Integrated from evolver-packages."""
TOOL_META = {"name": "dev-dashboard", "desc": "Developer dashboard: git, system, ports, processes — CLI+TUI", "func": "main"}

try:
    from dev_dashboard.cli import main
except ImportError:
    import sys
    sys.path.insert(0, "/root/evolver-packages/dev-dashboard/src")
    from dev_dashboard.cli import main
