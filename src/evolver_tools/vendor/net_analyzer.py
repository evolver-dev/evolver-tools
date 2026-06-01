"""net-analyzer — Network analysis (CLI+TUI). Integrated from evolver-packages."""
TOOL_META = {"name": "net-analyzer", "desc": "Network analysis: ping, trace, port scan, DNS — CLI+TUI", "func": "main"}

try:
    from net_analyzer.__main__ import main
except ImportError:
    import sys
    sys.path.insert(0, "/root/evolver-packages/net-analyzer/src")
    from net_analyzer.__main__ import main
