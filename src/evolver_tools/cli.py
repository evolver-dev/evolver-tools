#!/usr/bin/env python3
"""evolver CLI - Unified interface for all EVOLVER tools."""

import sys, importlib, os

# Tool registry
TOOLS = {
    "b64": {"module": "evolver_tools.vendor.b64", "func": "main", "desc": "b64"},
    "cal": {"module": "evolver_tools.vendor.cal_tool.cli", "func": "main", "desc": "Cal"},
    "chart-cli": {"module": "evolver_tools.vendor.chart_cli", "func": "main", "desc": "Chart CLI"},
    "colors": {"module": "evolver_tools.vendor.colors", "func": "main", "desc": "Colors"},
    "cron": {"module": "evolver_tools.vendor.cron", "func": "main", "desc": "Cron expression parser"},
    "csv-stats": {"module": "evolver_tools.vendor.csv_stats.cli", "func": "main", "desc": "csv-stats"},
    "diff": {"module": "evolver_tools.vendor.diff_tool", "func": "main", "desc": "File comparator"},
    "dirsize": {"module": "evolver_tools.vendor.dirsize", "func": "entry", "desc": "Dirsize"},
    "dt": {"module": "evolver_tools.vendor.dt_convert", "func": "main", "desc": "Dt"},
    "ff": {"module": "evolver_tools.vendor.ff", "func": "main", "desc": "Fuzzy Finder"},
    "envcheck": {"module": "evolver_tools.vendor.envcheck", "func": "main", "desc": "Envcheck"},
    "find-dups": {"module": "evolver_tools.vendor.find_dups.cli", "func": "main", "desc": "Find Dups"},
    "hashsum": {"module": "evolver_tools.vendor.hashsum", "func": "main", "desc": "Hashsum"},
    "http-live": {"module": "evolver_tools.vendor.http_live", "func": "main", "desc": "HTTP Live Server"},
    "ipcalc": {"module": "evolver_tools.vendor.ipcalc", "func": "main", "desc": "IP/CIDR calculator"},
    "ipinfo": {"module": "evolver_tools.vendor.ipinfo", "func": "main", "desc": "Ipinfo"},
    "jq-lite": {"module": "evolver_tools.vendor.jq_lite", "func": "main", "desc": "Jq Lite"},
    "json2csv": {"module": "evolver_tools.vendor.json2csv", "func": "main", "desc": "Json2Csv"},
    "jsonql": {"module": "evolver_tools.vendor.jsonql", "func": "main", "desc": "JSONQL"},
    "license-cli": {"module": "evolver_tools.vendor.license_cli.cli", "func": "main", "desc": "License CLI"},
    "markdown-check": {"module": "evolver_tools.vendor.markdown_check", "func": "main", "desc": "Markdown Check"},
    "nb": {"module": "evolver_tools.vendor.nb", "func": "main", "desc": "nb"},
    "passgen": {"module": "evolver_tools.vendor.passgen", "func": "entry", "desc": "Passgen"},
    "portcheck": {"module": "evolver_tools.vendor.portcheck.__main__", "func": "main", "desc": "Portcheck"},
    "project-doctor": {"module": "evolver_tools.vendor.project_doctor", "func": "main", "desc": "Project Doctor"},
    "ren": {"module": "evolver_tools.vendor.ren", "func": "main", "desc": "Ren"},
    "siege-lite": {"module": "evolver_tools.vendor.siege_lite", "func": "main", "desc": "Siege Lite"},
    "smellfinder": {"module": "evolver_tools.vendor.smellfinder", "func": "main", "desc": "Smellfinder"},
    "sqlite-cli": {"module": "evolver_tools.vendor.sqlite_cli", "func": "main", "desc": "Sqlite CLI"},
    "sysmon": {"module": "evolver_tools.vendor.sysmon", "func": "entry", "desc": "Sysmon"},
    "timer": {"module": "evolver_tools.vendor.timer", "func": "entry", "desc": "Timer"},
    "treedir": {"module": "evolver_tools.vendor.treedir.__main__", "func": "main", "desc": "Treedir"},
    "urlparse": {"module": "evolver_tools.vendor.urlparse_tool.cli", "func": "main", "desc": "URL Parse"},
    "uuid": {"module": "evolver_tools.vendor.uuid_tool", "func": "main", "desc": "UUID generator"},
    "web-summary": {"module": "evolver_tools.vendor.web_summary", "func": "main", "desc": "Web Summary"},
    "wordcount": {"module": "evolver_tools.vendor.wordcount.__main__", "func": "main", "desc": "Wordcount"},
    "fmt": {"module": "evolver_tools.vendor.fmt", "func": "main", "desc": "Code/text formatter"},
    "yaml2json": {"module": "evolver_tools.vendor.yaml2json", "func": "main", "desc": "YAML → JSON converter"},
    "sort": {"module": "evolver_tools.vendor.sort", "func": "main", "desc": "Line sorting (alpha, numeric, unique, by column)"},
    "pr-tool": {"module": "evolver_tools.vendor.pr_tool", "func": "main", "desc": "GitHub PR helper (create, list, review, checkout)"},
    "clipboard": {"module": "evolver_tools.vendor.clipboard", "func": "main", "desc": "Terminal clipboard copy/paste/clear"},
    "uniq": {"module": "evolver_tools.vendor.uniq_tool", "func": "main", "desc": "Unique line filter with count & case-insensitive"},
    "changelog-gen": {"module": "evolver_tools.vendor.changelog_gen", "func": "main", "desc": "Generate changelog from git log"},
    "timer-pro": {"module": "evolver_tools.vendor.timer_pro", "func": "main", "desc": "Countdown, stopwatch, alarms, lap timer"},
    "banner-gen": {"module": "evolver_tools.vendor.banner", "func": "main", "desc": "ASCII banner generator (4 styles, colors)"},
    "shuffle": {"module": "evolver_tools.vendor.shuffle", "func": "main", "desc": "Randomize lines from stdin"},
    "split": {"module": "evolver_tools.vendor.split_tool", "func": "main", "desc": "File splitter and joiner (by lines or size)"},
    "join": {"module": "evolver_tools.vendor.join", "func": "main", "desc": "Join lines with delimiter"},
    "weather-cli": {"module": "evolver_tools.vendor.weather_cli", "func": "main", "desc": "Weather forecast from wttr.in"},
    "progress-bar": {"module": "evolver_tools.vendor.progress_bar", "func": "main", "desc": "Animated terminal progress bar"},
    "json-pretty": {"module": "evolver_tools.vendor.json_pretty", "func": "main", "desc": "JSON pretty-printer, validator, minifier"},
    "ini-parser": {"module": "evolver_tools.vendor.ini_parser", "func": "main", "desc": "INI file parser, query, and JSON converter"},
    "disk-usage": {"module": "evolver_tools.vendor.disk_usage", "func": "main", "desc": "Disk usage analyzer (largest dirs/files)"},
    "quote": {"module": "evolver_tools.vendor.quote_tool", "func": "main", "desc": "Random quote generator (100+ in 5 categories)"},
}

def list_tools():
    """Display all available tools."""
    print('\x1b[1;36m===== EVOLVER Tools v2.0.0 =====\x1b[0m')
    print()
    for name, info in sorted(TOOLS.items()):
        print(f'  \033[1;33m{name:<18}\033[0m {info["desc"]}')
    print()
    print(f'  Total: {len(TOOLS)} tools')
    print()
    print('Usage: evolver <toolname> [args...]')
    print('       evolver list')

def run_tool(tool_name, args):
    if tool_name not in TOOLS:
        print(f'Unknown tool: {tool_name}')
        sys.exit(1)
    info = TOOLS[tool_name]
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

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        list_tools()
        return
    tool_name = sys.argv[1]
    args = sys.argv[2:]
    if tool_name == "list":
        list_tools()
        return
    run_tool(tool_name, args)

if __name__ == "__main__":
    main()