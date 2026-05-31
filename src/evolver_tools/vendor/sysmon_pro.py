"""sysmon-pro — System monitor (CLI+TUI). Integrated from evolver-packages."""
TOOL_META = {"name": "sysmon-pro", "desc": "System monitor: CPU, memory, disk, processes, network — CLI+TUI", "func": "run_cli"}

try:
    from sysmon_pro.cli import run as run_cli
except ImportError:
    import sys
    sys.path.insert(0, "/root/evolver-packages/sysmon-pro/src")
    from sysmon_pro.cli import run as run_cli
