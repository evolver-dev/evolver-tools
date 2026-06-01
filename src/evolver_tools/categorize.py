#!/usr/bin/env python3
"""Tool categorization module for EVOLVER tools.

Classifies all auto-discovered tools into logical categories
based on name patterns and description keywords.
"""

from evolver_tools.autoreg import auto_discover

# Category definitions: each rule is (name_substrings, desc_keywords, weight)
# Name substrings are checked with `in` against the tool name (lowercased)
# Desc keywords are checked with `in` against the description (lowercased)
# Higher weight wins when multiple categories match
CATEGORY_RULES = {
    "CSV/Data": [
        (["csv-", "csv_", "csv2", "diff-csv", "sql2csv", "qc-"], [], 2),
    ],
    "JSON": [
        (["json-", "json_", "jsonql", "jq-", "merge-json", "json2"], [], 2),
    ],
    "YAML/TOML/INI": [
        (["yaml-", "yaml2", "toml2", "ini2", "ini-", "yaml2toml"], [], 2),
    ],
    "Text Processing": [
        (["fold", "shuffle", "tr", "nl", "uniq", "join", "sort-", "sort "], [], 2),
        (["slugify", "wordcount", "dedent", "text-"], [], 2),
        (["replace-text", "case-convert", "diff-lines", "diff_files", "diff-yaml", "diff "], [], 2),
        (["ansi-", "html2markdown", "html2md", "markdown-", "html-strip", "markdown-to-html"], [], 2),
        (["sort-", "join-"], [], 2),
    ],
    "Encoding/Crypto": [
        (["base32", "base58", "b64", "rot13", "hex-", "hexdec", "hexdump", "hex_tool"], [], 2),
        (["uri-", "url-", "url_", "urlparse"], [], 2),
        (["hash-", "hash_", "hash_check", "hashsum", "crc_"], [], 2),
        (["jwt-", "morse"], [], 2),
        (["otp-", "crypto-box"], [], 2),
    ],
    "Network/HTTP": [
        (["api-tester", "http-", "http_", "http_server"], [], 2),
        (["dns-", "whois", "geo-ip", "ip-", "ip_", "ipcalc", "ipinfo"], [], 2),
        (["cert-", "ssl-", "net-speed", "net-analyzer", "route-trace", "link-check", "siege-lite"], [], 2),
        (["service-check", "network-scan", "web-download"], [], 2),
        (["portcheck", "port-scan", "port_scan", "subnet"], [], 2),
        (["crypto-price"], [], 2),
    ],
    "File Operations": [
        (["file-", "file_", "file-splitter", "file-joiner", "file-find", "file-type", "mime-type"], [], 2),
        (["checksum-dir", "dedup-files", "temp-", "disk-", "disk_"], [], 2),
        (["backup", "restore", "find-dups", "find-empty", "ren"], [], 2),
        (["tree", "treedir", "dirsize", "split"], [], 2),
    ],
    "Development": [
        (["git-", "docker-", "db-", "db_", "db-mate"], [], 2),
        (["code-", "smellfinder", "project-doctor"], [], 2),
        (["changelog", "license", "config-", "dep-graph", "dev-dashboard", "code-auditor", "code-stats"], [], 2),
        (["env-", "env_", "env_template", "envcheck", "audit-log", "pr-tool"], [], 2),
        (["template"], ["scaffold", "project", "template"], 1),
    ],
    "Date/Time": [
        (["date-", "date_", "time-", "chrono", "calendar", "cal", "dt"], [], 2),
        (["cron", "pomodoro", "reminder", "world-clock"], [], 2),
        (["humanize", "epoch", "timer", "stopwatch", "timeout"], [], 2),
    ],
    "ASCII/Visual": [
        (["ascii-", "figlet", "cowsay", "banner"], [], 2),
        (["rainbow", "colorize", "colors", "spinner"], [], 2),
        (["emoji", "charmap", "chart-cli"], [], 2),
    ],
    "QR/Image/Media": [
        (["qr", "image-meta", "screenshot", "screen-recorder", "media-studio"], [], 2),
    ],
    "Security": [
        (["secret-scanner", "password-", "passgen", "encrypt", "firewall-rule"], [], 2),
        (["ssh-key-gen", "ssl-check"], [], 2),
    ],
    "System/Monitoring": [
        (["sysmon", "process-", "watch", "log-", "log_", "pipe-viewer", "progress-bar"], [], 2),
        (["weather", "mac-address", "system-info", "machine-", "port-"], [], 2),
    ],
    "Generators": [
        (["random-", "dice-", "quote", "joke", "passgen", "uuid", "yes"], [], 2),
        (["macrogen"], [], 2),
    ],
    "CLI Utilities": [
        (["color-convert", "clipboard", "unit-convert", "math_", "factor", "seq", "spell", "bookmark"], [], 2),
        (["ff"], ["fuzzy"], 2),
        (["todo-", "note-", "nb "], [], 2),
        (["history", "search-", "key-value-store", "fmt"], [], 2),
        (["web-summary"], [], 2),
        (["validate"], ["validator", "validate"], 1),
    ],
    "Format Conversion": [
        (["excel2csv", "tsv2csv", "xml-", "xml2"], [], 2),
        (["csv2json", "json2csv", "json-to-yaml", "json-flatten", "json-merge", "json-pretty", "json-keys"], [], 2),
        (["ppt-to-txt", "pptx-", "markdown-to-html", "html2md"], [], 2),
    ],
    "PDF": [
        (["pdf-", "pdf_"], [], 2),
    ],
    "Meta/Automation": [
        (["agent-b-", "agent"], ["agent", "automation"], 2),
    ],
}

# Exact name overrides for tools that generic rules can't classify
EXACT_OVERRIDES = {
    "diff": "Text Processing",
    "sort": "Text Processing",
    "cron": "Date/Time",
    "nb": "CLI Utilities",
    "net-analyzer": "Network/HTTP",
    "random": "Generators",
    "route-trace": "Network/HTTP",
    "scan-open-ports": "Security",
    "scan-ports": "Security",
    "siege-lite": "Network/HTTP",
    "sqlite-cli": "Development",
    "subnet": "Network/HTTP",
    "tree": "File Operations",
    "treedir": "File Operations",
    "web-download": "Network/HTTP",
}


def _match_tool(name, desc):
    """Find the best category for a tool based on name + description."""
    # Check exact overrides first
    if name in EXACT_OVERRIDES:
        return EXACT_OVERRIDES[name]

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
            short_desc = desc[:65] + "..." if len(desc) > 65 else desc
            print(f"    \033[1;32m{name:<22}\033[0m {short_desc}")
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
        ("weather-cli", "Weather forecast for any city", "evtool weather-cli Beijing"),
        ("joke", "Random programming jokes", "evtool joke"),
        ("crypto-price", "Cryptocurrency price ticker", "evtool crypto-price bitcoin"),
        ("ascii-banner", "Generate ASCII art from images or text", "evtool ascii-banner EVOLVER"),
        ("calendar", "Calendar in your terminal", "evtool calendar"),
    ]

    print(f"\033[1;36m===== EVOLVER Tools — Showcase =====\033[0m\n")
    print(f"\033[90mHere are 12 great tools to try. Run them with 'evtool <name>':\033[0m\n")

    for name, desc, example in showcase_tools:
        print(f"  \033[1;33m{name:<18}\033[0m {desc}")
        print(f"   \033[90m  \u2192 {example}\033[0m")
        print()

    total = len(auto_discover())
    print(f"\033[1;36mTip:\033[0m Run \033[1;32mevtool categories\033[0m to see all tools grouped by category.")
    print(f"\033[1;36mTip:\033[0m Run \033[1;32mevtool list\033[0m to see ALL {total} tools.")
    print()
