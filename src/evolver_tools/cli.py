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
    """Return package version from __init__ or importlib.metadata."""
    try:
        from evolver_tools import __version__
        return __version__
    except ImportError:
        pass
    try:
        return _pkg_version("evolver-tools")
    except PackageNotFoundError:
        return "38.0.0"


def _print_header(version=None):
    """Print the EVOLVER header banner."""
    if version is None:
        version = _get_version()
    print(f'\x1b[1;36m===== EVOLVER Tools v{version} =====\x1b[0m')


def list_tools():
    """Display all available tools (full listing)."""
    tools = auto_discover()
    _print_header()
    print()
    for name, info in sorted(tools.items()):
        print(f'  \033[1;33m{name:<18}\033[0m {info["desc"]}')
    print()
    print(f'  Total: {len(tools)} tools')
    print()
    print('Usage: evtool <toolname> [args...]')
    print('       evtool categories        — browse by category')
    print('       evtool showcase          — featured tools')
    print('       evtool --version         — show version')
    print('       evtool --help            — this help')


def welcome_screen():
    """Show a compelling first-run welcome screen (default no-args)."""
    tools = auto_discover()
    from evolver_tools.categorize import categorize_all
    cats = categorize_all()
    ver = _get_version()

    total = len(tools)
    cat_count = len(cats)
    repo_url = "github.com/evolver-dev/evolver-tools"
    ver_line = f"EVOLVER Tools v{ver}"
    stat_line = f"{total} tools · {cat_count} categories · zero external deps"

    # Box width: interior width between ║ corners (W)
    # Lines:  ╔═══ ver ══════════════╗  (W = 4 + len(ver) + 1 + R)
    #         ║  stat_line           ║
    #         ║  MIT · url           ║
    #         ╚══════════════════════╝
    W = max(50, len(stat_line) + 4, len(ver_line) + 8, len(repo_url) + 10)

    # Build the top border: ╔═══ ver ══...══╗
    left_top = f"╔═══ {ver_line} "
    right_pad = W - len(left_top) - 1  # -1 for ╗
    top = f"{left_top}{'═' * right_pad}╗"

    # Content lines
    line2 = f"║  {stat_line}{' ' * (W - 4 - len(stat_line))}║"
    line3_url = f"MIT · {repo_url}"
    line3 = f"║  {line3_url}{' ' * (W - 4 - len(line3_url))}║"

    # Bottom border
    bottom = f"╚{'═' * (W - 2)}╝"

    # Header box
    print()
    print(f"  {top}")
    print(f"  {line2}")
    print(f"  {line3}")
    print(f"  {bottom}")
    print()

    # Quick start — try these
    print(f"  \033[1;33m\u2192 Try these right now:\033[0m")
    examples = [
        ('evtool ascii-banner "Evolver"', 'ASCII art banner generator'),
        ('evtool rainbow "hello world"', 'Rainbow-colored text'),
        ('evtool qrcode https://github.com/evolver-dev', 'QR code in terminal'),
        ('evtool cowsay "I am alive!"', 'Talking ASCII cow'),
        ('evtool crypto-price bitcoin', 'Live cryptocurrency price'),
    ]
    for cmd, desc in examples:
        print(f"    \033[1;32m{cmd:<49}\033[0m \033[90m# {desc}\033[0m")
    print()

    # Navigation
    print(f"  \033[1;33m\u2192 Explore:\033[0m")
    print(f"    \033[1;32mevtool categories\033[0m        \033[90m\u2014 browse {cat_count} categories\033[0m")
    print(f"    \033[1;32mevtool showcase\033[0m          \033[90m\u2014 12 featured tools with examples\033[0m")
    print(f"    \033[1;32mevtool list\033[0m              \033[90m\u2014 full {total}-tool listing\033[0m")
    print(f"    \033[1;32mevtool <toolname> --help\033[0m  \033[90m\u2014 per-tool usage\033[0m")
    print()

    # Tip
    tip = 'Pipe any tool output through "evtool clipboard copy" to copy it.'
    tip2 = 'Most tools accept stdin — try "echo test | evtool b64"'
    print(f"  \033[1;36m\u24d8 Tip:\033[0m {tip}")
    print(f"       {tip2}")
    print()


def run_tool(tool_name, args):
    tools = auto_discover()
    if tool_name not in tools:
        # Fuzzy matching: try hyphen↔underscore conversion
        alt_name = tool_name.replace('-', '_')
        if alt_name != tool_name and alt_name in tools:
            tool_name = alt_name
        else:
            alt_name2 = tool_name.replace('_', '-')
            if alt_name2 != tool_name and alt_name2 not in tools:
                alt_name2 = None
            if alt_name2 and alt_name2 in tools:
                tool_name = alt_name2
            else:
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
    if len(sys.argv) < 2:
        welcome_screen()
        return
    if sys.argv[1] in ("-h", "--help"):
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
