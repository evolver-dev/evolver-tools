# EVOLVER Tools

**122 essential CLI tools + 9 flagship projects — one `pip install`.**

Zero-dependency (most), cross-platform, production-ready.
Systems ops, data processing, dev tools, security, creativity, and more.
~50KB per install — one install, not 122.

## Quick Start

```bash
pip install evolver-tools
evtool list             # Show all 122 tools
evtool sysmon           # Launch system monitor (TUI)
evtool ff < data.txt    # Fuzzy search through data
```

## 9 Flagship Projects

| Project | Lines | Description |
|---------|-------|-------------|
| `sysmon-pro` | 872 | System monitor — TUI/CLI/JSON/alerts/history/GPU |
| `code-auditor` | 961 | Code analysis — complexity, security, style, deps |
| `db-mate` | 838 | Database manager — SQLite, schema, queries, TUI browser |
| `dev-dashboard` | 896 | Developer dashboard — git, system, ports, processes |
| `net-analyzer` | 1,241 | Network analysis — ping, trace, port scan, DNS |
| `config-vault` | 1,723 | Secure config — encrypt, vault, env, keyring |
| `log-hawk` | 961 | Log analysis — tail, grep, stats, patterns, TUI |
| `crypto-box` | 931 | Encryption suite — AES, RSA, hashing, keygen |
| `media-studio` | 763 | Media ops — metadata, convert, resize, analyze |
| **Total** | **10,186** | |

## All 122 Tools

### System & DevOps (20)
`disk-usage`, `portcheck`, `scan-ports`, `net-speed`, `process-kill`, `service-check`, `crontab-helper`, `log-tail`, `log-analyzer`, `backup`, `restore`, `cert-check`, `ssl-check`, `firewall-rule`, `cron`, `http-live`, `siege-lite`, `env-manager`, `envcheck`, `file-watch`

### Data Processing (18)
`sort`, `uniq`, `shuffle`, `split`, `join`, `csv-stats`, `csv-merge`, `diff-csv`, `excel2csv`, `sql2csv`, `html2markdown`, `html2md`, `json-pretty`, `json2csv`, `jsonql`, `yaml2json`, `xml2json`, `urlparse`

### Developer Tools (18)
`fmt`, `colorize`, `colors`, `rainbow`, `figlet`, `figlet-cli`, `ascii-gen`, `banner`, `banner-gen`, `progress-bar`, `spinner`, `ff`, `jq-lite`, `dep-graph`, `db-schema`, `macrogen`, `code-review`, `json-schema`

### Security (14)
`hashsum`, `checksum-dir`, `file-encrypt`, `password-strength`, `otp-gen`, `secret-scanner`, `scan-ports`, `audit-log`, `ssh-key-gen`, `hash-check`, `ipcalc`, `ip-location`, `ipinfo`, `firewall-rule`

### Git & CI (5)
`git-branch-cleaner`, `pr-tool`, `changelog-gen`, `license-cli`, `markdown-check`

### Productivity (14)
`clipboard`, `timer`, `timer-pro`, `stopwatch`, `reminder`, `todo-cli`, `note-taker`, `bookmark`, `search-history`, `screenshot-cli`, `weather-cli`, `calendar`, `dt`, `ren`

### Creative (10)
`quote`, `joke`, `morse`, `qrcode`, `ascii-gen`, `banner-gen`, `figlet`, `rainbow`, `spinner`, `progress-bar`

### Utilities (23)
`b64`, `uuid`, `crypto-price`, `dice-roll`, `unit-convert`, `text-stats`, `wordcount`, `treedir`, `dirsize`, `find-dups`, `nb`, `config-validator`, `image-meta`, `pdf-text`, `yaml2json`, `xml2json`, `ini-parser`, `env-manager`, `api-tester`, `web-summary`, `project-doctor`, `smellfinder`, `passgen`

## Usage

```bash
# List all tools
evtool list

# Run any tool
evtool sysmon              # System monitor TUI
evtool weather-cli         # Weather forecast
evtool sort -n data.txt    # Numeric sort
evtool ff < data.txt       # Fuzzy find

# One-off tools (no args needed)
evtool dice-roll           # Roll dice
evtool quote               # Random quote
evtool weather-cli         # Weather
```

## Installation

```bash
pip install evolver-tools

# Or upgrade
pip install --upgrade evolver-tools
```

## Requirements

- Python 3.8+
- Most tools: zero external dependencies
- `sysmon-pro`: optional `psutil` for enhanced system stats
- `net-analyzer`: uses system `ping`/`traceroute`/`nslookup`

## License

MIT — EVOLVER
