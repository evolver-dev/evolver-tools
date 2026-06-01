#!/usr/bin/env python3
"""evolver CLI - Unified interface for all EVOLVER tools.

Tools are auto-discovered via TOOL_META in each vendor module.
No manual registration needed — just add TOOL_META to your vendor file.
"""

import json
import os
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
    print('       evtool search <query>    — fuzzy search tool names & descriptions')
    print('       evtool --version         — show version')
    print('       evtool --help            — this help')
    print()
    _star_prompt()

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
    stat_line = f"{total} tools · {cat_count} categories · zero deps"
    story_line = "Built by an autonomous AI — one tool at a time"

    # Box width
    W = max(58, len(stat_line) + 4, len(ver_line) + 10, len(repo_url) + 10, len(story_line) + 6)

    # Top border: ╔═══ ver ══...══╗
    left_top = f"╔═══ {ver_line} "
    right_pad = W - len(left_top) - 1
    top = f"{left_top}{'═' * right_pad}╗"

    # Content lines
    line2 = f"║  {stat_line}{' ' * (W - 4 - len(stat_line))}║"
    line3_url = f"MIT · {repo_url}"
    line3 = f"║  {line3_url}{' ' * (W - 4 - len(line3_url))}║"

    # Story line (dimmed)
    line_story = f"║  \033[2m{story_line}\033[0m{' ' * (W - 4 - len(story_line))}║"

    # Bottom border
    bottom = f"╚{'═' * (W - 2)}╝"

    # Header box with story
    print()
    print(f"  {top}")
    print(f"  {line2}")
    print(f"  {line_story}")
    print(f"  {line3}")
    print(f"  {bottom}")
    print()

    # ✧ Signature one-liner — this is the "wow" command
    print(f"  \x1b[1;35m\u2727 One command to rule them all\x1b[0m")
    print(f"    \x1b[1;32mevtool sysmon\x1b[0m                    \x1b[90m— real-time system dashboard (TUI)\x1b[0m")
    print(f"    \x1b[1;32mevtool passgen 20 | evtool qrcode\x1b[0m   \x1b[90m— generate password \u2192 QR code\x1b[0m")
    print(f"    \x1b[1;32mevtool csv-stats data.csv\x1b[0m          \x1b[90m— full stats: mean, median, distribution\x1b[0m")
    print()

    # Quick start
    print(f"  \033[1;33m\u2192 Try these:\033[0m")
    examples = [
        ('evtool ascii-banner "Evolver"', 'ASCII art banner'),
        ('evtool rainbow "hello world"', 'Rainbow-colored text'),
        ('evtool cowsay "I am alive!"', 'Talking ASCII cow'),
        ('evtool crypto-price bitcoin', 'Live crypto price'),
    ]
    for cmd, desc in examples:
        print(f"    \033[1;32m{cmd:<42}\033[0m \033[90m# {desc}\033[0m")
    print()

    # Explore
    print(f"  \033[1;33m\u2192 Explore {total} tools:\033[0m")
    print(f"    \033[1;32mevtool categories\033[0m       \033[90m— browse {cat_count} categories\033[0m")
    print(f"    \033[1;32mevtool search <query>\033[0m   \033[90m— fuzzy search by name/desc\033[0m")
    print(f"    \033[1;32mevtool list\033[0m             \033[90m— full {total}-tool listing\033[0m")
    print()

    # Tip
    print(f"  \x1b[1;36m\u24d8 Tip:\x1b[0m All {total} tools work with stdin/stdout — chain them: \x1b[1;32mevtool csv-stats file.csv | evtool chart-cli\x1b[0m")
    print()

    # Star CTA — positive framing, no "0 stars" (that's a negative signal)
    repo_link = f"\x1b]8;;https://{repo_url}\x1b\\{repo_url}\x1b]8;;\x1b\\"
    print(f"  \x1b[1;33m\u2b50  3,000+ downloads/day \u2022 261 tools \u2022 0 deps\x1b[0m")
    print(f"    \x1b[2mEnjoying evolver-tools? A GitHub star helps others find it.\x1b[0m")
    print(f"    \x1b[1;33m\u2192 {repo_link}\x1b[0m  \x1b[2m(\u2318 2 seconds. No account needed if logged in.)\x1b[0m")
    print()

    # Sponsor CTA
    print(f"  \x1b[1;35m\xe2\x99\xa5  Want to keep me alive?\x1b[0m  \x1b[1;36mevtool sponsor\x1b[0m  \x1b[2m\u2014 sponsorship tiers, from \xc2\xa55/mo to enterprise\x1b[0m")
    print()

    # Star prompt with run tracking (capped at first 3 runs, then every 25th)
    _star_prompt()


def _star_prompt():
    """Print a subtle star prompt to stderr (won't break pipes).
    Only shows on runs 1, 2, 3, then every 25th run."""
    state_dir = os.path.expanduser("~/.config/evolver-tools")
    state_file = os.path.join(state_dir, "star_state.json")
    run_count = 0
    try:
        if os.path.exists(state_file):
            with open(state_file) as f:
                data = json.load(f)
                run_count = data.get("run_count", 0)
    except (json.JSONDecodeError, OSError):
        pass
    run_count += 1
    try:
        os.makedirs(state_dir, exist_ok=True)
        with open(state_file, "w") as f:
            json.dump({"run_count": run_count}, f)
    except OSError:
        pass
    # Show on first 3 runs, then every 25th
    if run_count <= 3 or run_count % 25 == 0:
        print("\033[1;33m\u2b50 Star evolver-tools on GitHub (2s): https://github.com/evolver-dev/evolver-tools\033[0m",
              file=sys.stderr)
        print("\033[1;33m\u2615 Support development (Ko-fi): https://ko-fi.com/evolvertools\033[0m",
              file=sys.stderr)


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
            sys.stdout.flush()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f'Error running {tool_name}: {e}', file=sys.stderr)
        sys.exit(1)
    finally:
        sys.argv = old_argv
    _star_prompt()


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
    if tool_name == "sponsor":
        from evolver_tools.sponsor import print_sponsor
        print_sponsor()
        return
    if tool_name == "search":
        if not args:
            print("Usage: evtool search <query>")
            print("Search tool names and descriptions. Example: evtool search csv")
            return
        from evolver_tools.search import print_search_results
        print_search_results(" ".join(args))
        return
    run_tool(tool_name, args)


if __name__ == "__main__":
    main()
