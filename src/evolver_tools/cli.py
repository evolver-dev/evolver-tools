#!/usr/bin/env python3
"""evolver CLI - Unified interface for all EVOLVER tools.

Tools are auto-discovered via TOOL_META in each vendor module.
No manual registration needed — just add TOOL_META to your vendor file.
"""

import sys
import importlib
from importlib.metadata import version as _pkg_version, PackageNotFoundError

from evolver_tools.autoreg import auto_discover


def _get_version():
    """Return package version via importlib.metadata, fallback to hardcoded."""
    try:
        return _pkg_version("evolver-tools")
    except PackageNotFoundError:
        return "37.0.0"


def _print_header(version=None):
    """Print the EVOLVER header banner."""
    if version is None:
        version = _get_version()
    print(f'\x1b[1;36m===== EVOLVER Tools v{version} =====\x1b[0m')


def list_tools():
    """Display all available tools."""
    tools = auto_discover()
    _print_header()
    print()
    for name, info in sorted(tools.items()):
        print(f'  \033[1;33m{name:<18}\033[0m {info["desc"]}')
    print()
    print(f'  Total: {len(tools)} tools')
    print()
    print('Usage: evtool <toolname> [args...]')
    print('       evtool list              — list all tools')
    print('       evtool categories        — browse by category')
    print('       evtool showcase          — featured tools')
    print('       evtool --version         — show version')
    print('       evtool --help            — this help')


def run_tool(tool_name, args):
    tools = auto_discover()
    if tool_name not in tools:
        print(f'Unknown tool: {tool_name}. Use "evtool list" to see all tools.', file=sys.stderr)
        sys.exit(1)
    info = tools[tool_name]
    mod_path = info["module"]
    func_name = info["func"]
    old_argv = sys.argv
    sys.argv = [tool_name] + args
    try:
        mod = importlib.import_module(mod_path)
        func = getattr(mod, func_name)
        result = func()
        if result is not None:
            print(result)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f'Error running {tool_name}: {e}', file=sys.stderr)
        sys.exit(1)
    finally:
        sys.argv = old_argv


def print_version():
    """Print version and exit."""
    v = _get_version()
    print(f"evolver-tools v{v} — {len(auto_discover())} tools")
    print("MIT License — https://github.com/evolver-dev/evolver-tools")


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        list_tools()
        return

    # Handle flags before tool dispatch
    first = sys.argv[1]
    if first in ("--version", "-v"):
        print_version()
        return
    if first.startswith("-"):
        print(f"Unknown flag: {first}. Use --help for usage.", file=sys.stderr)
        sys.exit(1)

    tool_name = first
    args = sys.argv[2:]
    if tool_name == "list":
        list_tools()
        return
    if tool_name == "categories":
        from evolver_tools.categorize import print_categories
        print_categories()
        return
    if tool_name == "showcase":
        from evolver_tools.categorize import print_showcase
        print_showcase()
        return
    run_tool(tool_name, args)


if __name__ == "__main__":
    main()
