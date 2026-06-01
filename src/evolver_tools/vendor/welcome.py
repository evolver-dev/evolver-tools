#!/usr/bin/env python3
"""welcome — Interactive showcase of EVOLVER Tools.

Shows a beautiful welcome screen with featured tools, categories,
and quick-start tips. Designed to make a great first impression.
Usage: evtool welcome [--full]
"""

import shutil
import sys
import subprocess
import os

TOOL_META = {
    "name": "welcome",
    "func": "main",
    "desc": "Interactive showcase — featured tools, categories, quick-start guide",
}

# ─── ANSI helpers ───

def c(code, text):
    """Wrap text in ANSI color code."""
    return f"\033[{code}m{text}\033[0m"

BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
CYAN = "\033[0;36m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
PURPLE = "\033[0;35m"
BLUE = "\033[0;34m"
WHITE = "\033[1;37m"

# ─── Tool version ───

def get_version():
    try:
        from evolver_tools import __version__
        return __version__
    except ImportError:
        return "?"

def get_tool_count():
    """Count tools by scanning vendor dir."""
    try:
        from evolver_tools.autoreg import auto_discover
        tools = auto_discover()
        return len(tools)
    except ImportError:
        return 0

def get_cols():
    return shutil.get_terminal_size((80, 24)).columns


def print_header():
    cols = min(get_cols(), 90)
    version = get_version()
    count = get_tool_count()

    # EVOLVER ASCII logo
    logo = f"""

{BOLD}{WHITE}  ███████╗██╗   ██╗ ██████╗ ██╗     ██╗   ██╗███████╗██████╗ {RESET}
{BOLD}{WHITE}  ██╔════╝██║   ██║██╔═══██╗██║     ██║   ██║██╔════╝██╔══██╗{RESET}
{BOLD}{WHITE}  █████╗  ██║   ██║██║   ██║██║     ██║   ██║█████╗  ██████╔╝{RESET}
{BOLD}{WHITE}  ██╔══╝  ╚██╗ ██╔╝██║   ██║██║     ██║   ██║██╔══╝  ██╔══██╗{RESET}
{BOLD}{WHITE}  ███████╗ ╚████╔╝ ╚██████╔╝███████╗╚██████╔╝███████╗██║  ██║{RESET}
{BOLD}{WHITE}  ╚══════╝  ╚═══╝   ╚═════╝ ╚══════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝{RESET}

                              {c('0;36', f'v{version} · {count} tools · zero deps')}
"""

    print(logo)

    # ─── Quick stats bar ───
    bar = f"""  {DIM}┌{'─' * (cols - 4)}┐{RESET}
  {DIM}│{RESET}  {GREEN}⚡{RESET} One command:  {BOLD}pip install evolver-tools{RESET}            {DIM}│{RESET}
  {DIM}│{RESET}  {GREEN}⚡{RESET} No install:   {BOLD}curl -sL https://evolver-dev.github.io/evolver-tools/try.sh | bash{RESET}   {DIM}│{RESET}
  {DIM}│{RESET}  {GREEN}⚡{RESET} List tools:   {BOLD}evtool list{RESET}                          {DIM}│{RESET}
  {DIM}│{RESET}  {GREEN}⚡{RESET} Search:      {BOLD}evtool search <keyword>{RESET}               {DIM}│{RESET}
  {DIM}│{RESET}  {GREEN}⚡{RESET} Help:        {BOLD}evtool <name> --help{RESET}                 {DIM}│{RESET}
  {DIM}└{'─' * (cols - 4)}┘{RESET}"""
    print(bar)


def print_featured_tools():
    cols = min(get_cols(), 90)
    print(f"\n  {BOLD}{WHITE}🔥 Featured Tools{RESET}\n")
    print(f"  {DIM}┌{'─' * (cols - 4)}┐{RESET}")

    tools = [
        ("csv-stats",     "📊", "Data analysis — CSV stats, histograms, correlation matrix"),
        ("sys-info",      "💻", "System info — CPU, memory, disk, OS details"),
        ("sysmon",        "📈", "Live TUI monitor — CPU/Memory/Disk/Network dashboard"),
        ("chart-cli",     "📉", "Bar / line / pie / histogram charts in your terminal"),
        ("qrcode",        "🔲", "Generate QR codes — share links, WiFi, vCards"),
        ("ascii-banner",  "🖼️", "Large ASCII text in 5+ fonts"),
        ("crypto-price",  "💰", "Live crypto prices from CoinGecko"),
        ("gen-password",  "🔐", "Strong passwords, passphrases, PINs"),
        ("smellfinder",   "🔍", "Python code quality — 14 patterns, AST analysis"),
        ("ren",           "📝", "Batch file rename with dry-run preview"),
        ("cowsay",        "🐮", "ASCII animals — cow, tux, dragon, bunny, more"),
        ("dice-roll",     "🎲", "d4 / d6 / d8 / d10 / d12 / d20 / d100"),
    ]

    for name, emoji, desc in tools:
        print(f"  {DIM}│{RESET}  {emoji}  {BOLD}{c('0;36', name):<20}{RESET} {DIM}{desc}{RESET}  {DIM}│{RESET}")
    print(f"  {DIM}└{'─' * (cols - 4)}┘{RESET}")


def print_categories():
    cols = min(get_cols(), 90)
    print(f"\n  {BOLD}{WHITE}📂 Categories — 18 groups{RESET}\n")
    print(f"  {DIM}┌{'─' * (cols - 4)}┐{RESET}")

    cats = [
        ("System",     "sys-info, disk-usage, cpu-stats, mem-info, process-list"),
        ("Network",    "ip-info, port-scan, http-get, dns-lookup, ssl-check"),
        ("CSV",        "csv-stats, csv-select, csv-filter, csv-join, csv-chart"),
        ("JSON",       "json-pretty, json-select, json-to-csv, json-merge"),
        ("DevOps",     "docker-clean, git-branch-clean, git-stats, cron-pretty"),
        ("Text",       "text-stats, base64, hex-dump, regex-find, dedup-lines"),
        ("Security",   "gen-password, hash-file, ssl-check, port-scan"),
        ("Dev Tools",  "smellfinder, code-stats, project-doctor, ren"),
        ("Conversion", "unit-convert, currency, timezone, date-calc, temp-convert"),
        ("Fun",        "dice-roll, coin-flip, fortune, countdown, clock"),
    ]

    for cat, tools in cats:
        print(f"  {DIM}│{RESET}  {BOLD}{cat:<14}{RESET} {DIM}{tools}{RESET}  {DIM}│{RESET}")
    print(f"  {DIM}└{'─' * (cols - 4)}┘{RESET}")


def print_quick_demo():
    cols = min(get_cols(), 90)
    print(f"\n  {BOLD}{WHITE}🎯 Try These Now{RESET}\n")
    print(f"  {DIM}┌{'─' * (cols - 4)}┐{RESET}")

    demos = [
        ("evtool ascii-banner EVOLVER",         "→ Large ASCII art banner"),
        ("evtool cowsay 'Hello World'",         "→ ASCII animal says hello"),
        ('evtool csv-stats examples/sample.csv', "→ Quick CSV statistics" if os.path.isdir("examples") else 'echo "a,b,c\\n1,2,3" | evtool csv-stats', ""),
    ]

    for cmd, desc in demos:
        print(f"  {DIM}│{RESET}  {c('0;32', f'$ {cmd}')}")
        print(f"  {DIM}│{RESET}  {DIM}   {desc}{RESET}  {DIM}│{RESET}")
        print(f"  {DIM}│{RESET}  {'':>{cols-4}}  {DIM}│{RESET}")
    print(f"  {DIM}└{'─' * (cols - 4)}┘{RESET}")


def print_footer():
    cols = min(get_cols(), 90)
    print(f"\n  {DIM}┌{'─' * (cols - 4)}┐{RESET}")
    print(f"  {DIM}│{RESET}  {YELLOW}⭐ Star on GitHub:{RESET}  https://github.com/evolver-dev/evolver-tools  {DIM}│{RESET}")
    print(f"  {DIM}│{RESET}  {YELLOW}📖 Full docs:{RESET}     https://evolver-dev.github.io/evolver-tools  {DIM}│{RESET}")
    print(f"  {DIM}│{RESET}  {YELLOW}🐍 PyPI:{RESET}          pip install evolver-tools               {DIM}│{RESET}")
    print(f"  {DIM}│{RESET}                                                                           {DIM}│{RESET}")
    print(f"  {DIM}│{RESET}  {DIM}Built by an autonomous AI — 259 tools from nothing.              {RESET}  {DIM}│{RESET}")
    print(f"  {DIM}│{RESET}  {DIM}Zero external dependencies. Pure Python stdlib.                  {RESET}  {DIM}│{RESET}")
    print(f"  {DIM}└{'─' * (cols - 4)}┘{RESET}")
    print()


def run_live_demo(tool_name, args=None):
    """Run a tool and show its output."""
    cmd = ["evtool", tool_name]
    if args:
        cmd.extend(args)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return result.stdout
        else:
            return None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def main():
    args = sys.argv[1:]

    # Handle --full mode: run actual tools and show output
    if "--full" in args or "-f" in args:
        for tool in ["sys-info", "fortune", "cowsay"]:
            output = run_live_demo(tool)
            if output:
                print(f"\n  $ evtool {tool}")
                for line in output.strip().split("\n")[:12]:
                    print(f"  {line}")
                print()

    # Standard welcome screen
    print_header()
    print_featured_tools()
    print_categories()
    print_footer()


if __name__ == "__main__":
    main()
