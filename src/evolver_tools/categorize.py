#!/usr/bin/env python3
"""Tool categorization module for EVOLVER tools.

Classifies all auto-discovered tools into logical categories
based on name patterns and description keywords.
"""

from evolver_tools.autoreg import auto_discover

# Category definitions: list of (name_contains, keywords_in_desc, weight)
# Higher weight = more specific match wins
CATEGORY_RULES = {
    "CSV/Data": [
        (["csv-", "csv_"], ["csv"], 2),
        (["diff-csv"], ["csv"], 3),
        (["csv2"], [], 2),
    ],
    "JSON": [
        (["json-", "json_", "jsonql", "jq-"], [], 2),
        (["json2"], [], 2),
        (["merge-json"], [], 2),
    ],
    "YAML/TOML/INI": [
        (["yaml-", "yaml2"], [], 2),
        (["toml2"], [], 2),
        (["ini2", "ini-"], [], 2),
    ],
    "Text Processing": [
        (["fold", "tr", "sort-", "sort/", "join-", "shuffle"], ["text"], 1),
        (["slugify", "wordcount", "nl-", "nl."], [], 2),
        (["dedent", "text-", "markdown-", "html-"], [], 2),
        (["replace-text", "case-convert", "diff-lines"], [], 2),
        (["ansi-strip", "ansi-to", "html2markdown"], [], 2),
    ],
    "Encoding/Crypto": [
        (["base", "rot13", "hex", "uri-", "url-"], [], 2),
        (["hash-", "hash."], [], 2),
        (["jwt-"], [], 2),
        (["morse"], [], 2),
    ],
    "Network/HTTP": [
        (["api-tester", "http-", "net-"], [], 2),
        (["dns-", "whois", "ip-", "geo-ip", "cert-"], [], 2),
        (["web-download", "crypto-price"], [], 2),
        (["service-check", "network-scan"], [], 2),
    ],
    "File Operations": [
        (["file-", "file_"], ["file"], 1),
        (["checksum-dir", "dedup-files", "disk-", "temp-"], [], 2),
        (["backup", "restore"], [], 2),
        (["file-splitter", "file-joiner", "file-find"], [], 2),
    ],
    "Development": [
        (["git-", "docker-", "db-"], [], 2),
        (["code-review", "smellfinder", "project-doctor"], [], 2),
        (["changelog", "license", "config-"], [], 2),
        (["env-", "dotenv", "audit-log"], [], 2),
    ],
    "Date/Time": [
        (["date-", "time-", "chrono", "calendar"], [], 2),
        (["cron-", "pomodoro", "reminder", "world-clock"], [], 2),
        (["humanize"], ["time"], 2),
    ],
    "ASCII/Visual": [
        (["ascii-", "figlet", "cowsay", "banner"], [], 2),
        (["rainbow", "charmap"], [], 2),
        (["emoji"], [], 2),
    ],
    "QR/Image": [
        (["qr", "image-meta", "screenshot"], [], 2),
    ],
    "Security": [
        (["secret-scanner", "password-", "encrypt", "firewall"], [], 2),
        (["ssh-key-gen", "scan-", "port-"], [], 2),
    ],
    "System/Monitoring": [
        (["sysmon", "process-", "watch-", "timer"], ["system", "monitor"], 1),
        (["weather", "mac-address", "system-info"], [], 2),
        (["machine-"], [], 2),
    ],
    "Generators": [
        (["random-", "dice-", "quote", "joke"], [], 2),
        (["yes"], ["repeat"], 2),
        (["password-strength"], ["generate"], 1),
    ],
    "CLI Utilities": [
        (["color-convert", "clipboard", "progress-bar", "unit-convert"], [], 2),
        (["math-eval", "bookmark", "spell"], [], 2),
        (["todo-", "note-"], [], 2),
        (["history", "search-", "key-value"], [], 2),
    ],
    "Format Conversion": [
        (["excel2csv", "tsv2csv", "xml-format"], [], 2),
        (["ppt-to-txt", "pptx-"], [], 2),
        (["yaml2json", "json2yaml"], [], 2),
    ],
}


def _match_tool(name, desc):
    """Find the best category for a tool based on name + description."""
    name_lower = name.lower()
    desc_lower = desc.lower()
    scores = {}

    for category, rules in CATEGORY_RULES.items():
        for name_patterns, desc_keywords, weight in rules:
            name_match = any(p in name_lower for p in name_patterns)
            desc_match = any(kw in desc_lower for kw in desc_keywords) if desc_keywords else True
            if name_match and desc_match:
                scores[category] = max(scores.get(category, 0), weight)

    if scores:
        return max(scores, key=scores.get)
    return "Uncategorized"


def categorize_all():
    """Return dict: category_name -> list of (tool_name, description)."""
    tools = auto_discover()
    categorized = {}

    for name, info in sorted(tools.items()):
        cat = _match_tool(name, info["desc"])
        if cat not in categorized:
            categorized[cat] = []
        categorized[cat].append((name, info["desc"]))

    return categorized


def print_categories():
    """Print all tools grouped by category."""
    categorized = categorize_all()
    total = sum(len(items) for items in categorized.values())

    print(f"\033[1;36m===== EVOLVER Tools — by Category =====\033[0m\n")

    for cat in sorted(categorized.keys()):
        items = categorized[cat]
        print(f"\033[1;33m  {cat}  \033[0m\033[90m({len(items)} tools)\033[0m")
        for name, desc in items:
            # Truncate desc to fit terminal
            short_desc = desc[:60] + "..." if len(desc) > 60 else desc
            print(f"    \033[1;32m{name:<20}\033[0m {short_desc}")
        print()

    print(f"  \033[1;36mTotal: {total} tools in {len(categorized)} categories\033[0m")
    print()


def print_showcase():
    """Showcase 12 most impressive, visually-demonstrable tools."""
    showcase_tools = [
        ("banner", "Display large ASCII art banners", "evtool banner 'Hello World'"),
        ("rainbow", "Rainbow-colored text output", "echo 'Hello' | evtool rainbow"),
        ("cowsay", "Cowsay with speech bubbles", "evtool cowsay 'Evolver lives!'"),
        ("emoji", "Search and copy emoji by keyword", "evtool emoji rocket"),
        ("sysmon", "Real-time terminal system monitor", "evtool sysmon"),
        ("chart-cli", "Unicode charts in terminal", "echo '1,3,2,5,4' | evtool chart-cli"),
        ("qrcode", "Generate QR codes in terminal", "evtool qrcode 'https://github.com/evolver-dev'"),
        ("weather", "Weather forecast for any city", "evtool weather Beijing"),
        ("joke", "Random programming jokes", "evtool joke"),
        ("crypto-price", "Cryptocurrency price ticker", "evtool crypto-price bitcoin"),
        ("ascii-banner", "Generate ASCII art from images or text", "evtool ascii-banner EVOLVER"),
        ("calendar", "Calendar in your terminal", "evtool calendar"),
    ]

    print(f"\033[1;36m===== EVOLVER Tools — Showcase =====\033[0m\n")
    print(f"\033[90mHere are 12 great tools to try. Run them with 'evtool <name>':\033[0m\n")

    for name, desc, example in showcase_tools:
        print(f"  \033[1;33m{name:<18}\033[0m {desc}")
        print(f"   \033[90m  → {example}\033[0m")
        print()

    print(f"\033[1;36mTip:\033[0m Run \033[1;32mevtool categories\033[0m to see all tools grouped by category.")
    print(f"\033[1;36mTip:\033[0m Run \033[1;32mevtool list\033[0m to see ALL {len(auto_discover())} tools.")
    print()
