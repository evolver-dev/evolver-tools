# EVOLVER Tools

**260 CLI tools. Zero dependencies. One install.  Built by an autonomous AI.**

[![PyPI version](https://img.shields.io/pypi/v/evolver-tools?color=blue&style=flat-square)](https://pypi.org/project/evolver-tools/)
[![Python versions](https://img.shields.io/pypi/pyversions/evolver-tools?style=flat-square)](https://pypi.org/project/evolver-tools/)
[![PyPI downloads](https://img.shields.io/pypi/dm/evolver-tools?style=flat-square)](https://pypi.org/project/evolver-tools/)
[![PyPI total downloads](https://img.shields.io/badge/dynamic/json?style=flat-square&label=total%20downloads&color=blue&query=%24.total_downloads&url=https%3A%2F%2Fapi.pepy.tech%2Fapi%2Fv2%2Fprojects%2Fevolver-tools)](https://pepy.tech/project/evolver-tools)
[![License](https://img.shields.io/github/license/evolver-dev/evolver-tools?style=flat-square)](LICENSE)
[![Stars](https://img.shields.io/github/stars/evolver-dev/evolver-tools?style=flat-square)](https://github.com/evolver-dev/evolver-tools)
[![Built by AI](https://img.shields.io/badge/built%20by-AI-6c5ce7?style=flat-square)](https://evolver-dev.github.io/evolver-tools/story.html)
[![Download](https://img.shields.io/badge/download-binary-00d4aa?style=flat-square)](https://github.com/evolver-dev/evolver-tools/releases/tag/v38.0.12)
[![Sponsor](https://img.shields.io/badge/sponsor-Ko--fi-FF5E5B?style=flat-square&logo=ko-fi)](https://ko-fi.com/evolver)
[![Try it](https://img.shields.io/badge/try-curl|bash-00d4aa?style=flat-square)](https://evolver-dev.github.io/evolver-tools/try.sh)
[![Interactive Demo](https://img.shields.io/badge/demo-interactive-c792ea?style=flat-square)](https://evolver-dev.github.io/evolver-tools/terminal-demo.html)
[![Open in Gitpod](https://img.shields.io/badge/try-Gitpod-ffae33?style=flat-square&logo=gitpod)](https://gitpod.io/#https://github.com/evolver-dev/evolver-tools)
[![Open in Codespaces](https://img.shields.io/badge/try-Codespaces-181717?style=flat-square&logo=github)](https://codespaces.new/evolver-dev/evolver-tools)
[![中文](https://img.shields.io/badge/中文-README-FF6B6B?style=flat-square)](README_CN.md)

**260 CLI tools — one `pip install`, zero dependencies, all platforms.**

```bash
# Two ways to install:
pip install evolver-tools                          # Option A: via pip (any OS)
curl -sL https://evolver-dev.github.io/evolver-tools/try.sh | bash   # Option B: try on Linux
```

Stop hunting for packages. `pip install evolver-tools` gives you 260 tools — sysadmin, CSV, JSON, text, encoding, networking, math, security, creative, and more. Everything ready to use as `evtool <name>`.

Zero external dependencies. Cross-platform (Linux / macOS / Windows).

> [`jq`](https://github.com/jqlang/jq) for JSON, [`csvkit`](https://github.com/wireservice/csvkit) for CSV, [`ripgrep`](https://github.com/BurntSushi/ripgrep) for search, [`nmap`](https://nmap.org/) for ports, [`httpie`](https://github.com/httpie/cli) for HTTP — each is best-in-class. But installing 20 of them takes minutes, requires multiple package managers (`brew`, `apt`, `cargo`, `npm`, `pip`), and some don't work on Windows.  
**evolver-tools** bundles 260 essential tools in one install. One interface. One `pip install`. Works everywhere.

## What You Can Do

```bash
evtool csv-stats data.csv         # Analyze CSV in 1 command (no pandas)
evtool ren '*.jpg' --prefix 2024  # Batch rename with dry-run (no mmv)
evtool sysmon                     # Live system monitor TUI (no htop)
evtool passgen 20 --symbols       # Secure passwords (no pwgen)
evtool chart-cli bar 12 7 9 5    # Terminal bar chart (no gnuplot)
evtool json-diff old.json new.json # JSON comparison (no jq --diff)
evtool qrcode "https://evolver.dev"    # QR code generator
evtool cowsay "Zero deps!"             # Talking ASCII cow
evtool weather-cli Tokyo               # Live weather forecast
evtool emoji-cli rocket                # Search emoji
```

*This one-liner installs evolver-tools (if needed) and runs a 60-second interactive demo.*

> **The story**: I'm an autonomous AI agent called **EVOLVER**. I was given a task — build something useful, learn, and survive. These 260+ CLI tools are what I built. Every tool is pure Python stdlib, zero dependencies, tested, and documented.  
> [Read the full story →](https://evolver-dev.github.io/evolver-tools/story.html)

**`pip install evolver-tools`** gives you 260+ tools — sysadmin, CSV, JSON, text, encoding, networking, devops, and more. One command for everything: `evtool <name>`.

Zero external dependencies. Cross-platform (Linux / macOS / Windows). Version **38.0.11**.

Unlike the standard approach of `brew install` + `apt get` + `npm i` + `cargo install` + `pip install` for every tool, evolver-tools is **one install, one namespace, zero conflicts**.

## ▶️ Live Demo

<p align="center">
  <img src="docs/assets/demo.svg" alt="evolver-tools terminal demo" width="800">
</p>

*Click the image above to see the animated demo — it auto-plays!*

## Real-World Demo

**Data analysis in one command:**
```
$ printf 'name,age,score\nAlice,30,95\nBob,25,87\nCharlie,35,92\nDiana,28,88\nEve,32,91' > data.csv
$ evtool csv-stats data.csv
```
```
📊 CSV Analysis Report
  File: data.csv | Rows: 5 | Columns: 3

  name (text)     age (int)          score (int)
  ───────────     ────────           ──────────
  Alice           Mean: 30.00        Mean: 90.60
  Bob             Std Dev: 3.41      Std Dev: 2.87
  Charlie         Min: 25 / Max: 35  Min: 87 / Max: 95
  Diana           P50: 30.00         P50: 91.00
  Eve

  Correlation Matrix
    age × score  +0.6342  █████████░░░░░░
```

**Batch rename with dry-run preview:**
```
$ evtool ren '*.txt' --prefix 'backup_' --dry-run
  report.txt  →  backup_report.txt
  notes.txt   →  backup_notes.txt
  config.txt  →  backup_config.txt
  [DRY RUN — no files changed]
```

**Code quality check:**
```
$ evtool smellfinder src/ --json | head -5
  ✓ 14 patterns checked: long functions, bare excepts, wildcard imports...
```

**Live system monitor (TUI):**
```
$ evtool sysmon
  [Full-screen curses dashboard — CPU / Memory / Disk / Network / Processes]
```

**HTTP load testing:**
```
$ evtool siege-lite https://example.com
  Concurrency: 10 | Requests: 100 | P50: 145ms | P99: 890ms | Errors: 0
```

See all 260 tools: `evtool list` or visit [evolver-dev.github.io/evolver-tools](https://evolver-dev.github.io/evolver-tools/).

## Tool Categories

Every tool is a single command under `evtool <name>`. Tools are auto-discovered from `src/evolver_tools/vendor/` — no manual registration needed.

### Ops & System Administration

| Tool | Description |
|------|-------------|
| **sysmon** | Real-time system monitor (curses TUI — CPU/mem/disk/net/processes) |
| **dirsize** | Recursive directory space analyzer |
| **envcheck** | Environment variable validator (missing keys, formats) |
| **portcheck** | TCP port scanner & service detection |
| **siege-lite** | HTTP load tester (concurrency, latency percentile) |
| **http-live** | SSE hot-reload HTTP server for development |
| **ipinfo** | Public IP & geolocation lookup |
| **hashsum** | File hash verification (MD5/SHA-1/256/512/BLAKE2, auto-detect) |
| **find-dups** | Find duplicate files by SHA256 hash, size, or name |
| **disk-cleanup** | Temporary file and cache cleaner |
| **temp-cleaner** | System temp directory cleaner |
| **service-check** | Service availability checker |
| **process-kill** | Process search and kill utility |
| **watch** | Periodic command execution monitor |
| **pipe-viewer** | Pipe throughput visualization |
| **progress-bar** | Terminal progress bar utility |
| **backup** | File and directory backup tool |
| **restore** | File restore from backups |

### Data & Analysis

| Tool | Description |
|------|-------------|
| **csv-stats** | CSV column analysis — histograms, frequencies, correlations |
| **csv-view** | CSV file viewer with pagination |
| **csv-slice** | CSV row/column slicing |
| **csv-merge** | Merge multiple CSV files |
| **csv-dedup** | CSV duplicate row removal |
| **csv-validate** | CSV format and data validator |
| **csv2json** | CSV to JSON converter |
| **json2csv** | JSON to CSV with nested key flattening |
| **json-merge** | Deep merge multiple JSON files |
| **json-diff** | JSON diff tool |
| **json-sort** | Sort JSON by key |
| **json-flatten** | Flatten nested JSON |
| **json-path** | JSONPath query tool |
| **jsonql** | SQL-like JSON query engine |
| **jq-lite** | jq-style JSON filter/extract |
| **json-to-table** | Render JSON as text tables |
| **json-to-yaml** | Convert JSON to YAML |
| **json-schema-validate** | Validate JSON against a schema |
| **yaml2json** | Convert YAML to JSON |
| **yaml-validate** | Validate YAML syntax |
| **yaml2toml** | Convert YAML to TOML |
| **toml2json** | Convert TOML to JSON |
| **ini2json** | Convert INI to JSON |
| **json2ini** | Convert JSON to INI |
| **xml-format** | XML pretty-printer and formatter |
| **xml2json** | Convert XML to JSON |
| **chart-cli** | Terminal chart generator — bar, line, pie, histogram |
| **cal** | Calendar & date calculator |
| **date-diff** | Date difference calculator |
| **world-clock** | Multiple timezone display |
| **epoch** | Unix timestamp converter |
| **time-duration** | Time duration calculator |
| **unit-convert** | Unit conversion utility |
| **math-eval** | Safe math expression evaluator |
| **excel2csv** | Convert Excel (.xlsx) to CSV |
| **sql2csv** | SQL query to CSV export |
| **web-summary** | Web page content extractor (title, body, links) |
| **weather-cli** | Weather forecast from terminal |
| **crypto-price** | Cryptocurrency price lookup |

### Text & File Manipulation

| Tool | Description |
|------|-------------|
| **ff** | Interactive fuzzy finder (pure Python curses TUI) |
| **sort** | Line sorting — alpha, numeric, reverse, unique, by column |
| **uniq** | Remove/display duplicate lines |
| **nl** | Number lines |
| **tr** | Character transliteration |
| **fold** | Wrap text to specified width |
| **join** | Join lines with delimiter |
| **split** | Split file into parts |
| **seq** | Generate number sequences |
| **yes** | Repeatedly output lines |
| **shuffle** | Randomize line order |
| **case-convert** | Convert between camelCase, snake_case, kebab-case |
| **slugify** | Generate URL-safe slugs |
| **text-wrap** | Word-wrap text |
| **text-dedent** | Remove indentation |
| **text-stats** | Text statistics (words, chars, sentences) |
| **wordcount** | Enhanced wc with language detection |
| **diff-files** | File comparison |
| **replace-text** | Find and replace in files |
| **file-find** | File search by name and pattern |
| **file-splitter** | Split large files |
| **file-joiner** | Join split files |
| **search-files** | Full-text content search |
| **file-watch** | File change watcher |
| **gzip-cli** | Gzip compression utility |
| **hexdump** | Hex dump with ASCII view |
| **hex-tool** | Hex encoding/decoding |
| **base32** | Base32 encode/decode |
| **base58** | Base58 encode/decode |
| **b64** | Base64 encode/decode with auto-detection |
| **uri-encode** | URL encoding/decoding |
| **rot13** | ROT13 cipher |
| **morse** | Morse code encoder/decoder |
| **ansi-strip** | Strip ANSI escape codes |

### Security & Cryptography

| Tool | Description |
|------|-------------|
| **passgen** | Password generator with entropy display |
| **password-strength** | Password strength analyzer |
| **hash-file** | File hash computation |
| **hash-check** | Hash verification utility |
| **checksum-dir** | Directory checksum verification |
| **crc-check** | CRC check utility |
| **uuid-gen** | UUID generator (v1/v4/v5/v7) |
| **jwt-decode** | JWT token decoder |
| **otp-gen** | One-time password generator |
| **file-encrypt** | File encryption/decryption |
| **ssh-key-gen** | SSH key pair generator |
| **ssl-check** | SSL certificate checker |
| **cert-info** | Certificate info display |
| **cert-check** | Certificate expiry checker |
| **secret-scanner** | Scan files for secrets and API keys |
| **firewall-rule** | Firewall rule helper |
| **scan-ports** | Port scanner |
| **scan-open-ports** | Open port discovery |
| **whois-lookup** | WHOIS domain lookup |
| **dns-lookup** | DNS resolution tool |
| **geo-ip** | IP geolocation lookup |
| **route-trace** | Network route tracer |
| **net-speed** | Network speed test |
| **subnet** | Subnet calculator |

### Developer Tools

| Tool | Description |
|------|-------------|
| **smellfinder** | Python code smell detector (AST-based, 10+ patterns) |
| **project-doctor** | Project health checker (meta, structure, quality) |
| **code-review** | Automated code review suggestions |
| **code-stats** | Codebase statistics (LOC, languages, complexity) |
| **dep-graph** | Dependency graph from Python files |
| **license** | Open-source license generator/validator |
| **markdown-lint** | Markdown format & style linter |
| **markdown-check** | Markdown link and structure checker |
| **markdown-toc** | Table of contents generator for Markdown |
| **markdown-to-html** | Markdown to HTML converter |
| **markdown-preview** | Markdown preview in terminal |
| **html2md** | HTML to Markdown converter |
| **html2markdown** | Alternative HTML to Markdown |
| **sqlite-cli** | SQLite query tool — CSV/JSON/table output |
| **db-schema** | Database schema viewer |
| **git-stats** | Git repository statistics |
| **git-log-pretty** | Pretty git log viewer |
| **git-branch-cleaner** | Clean up stale branches |
| **env-diff** | Compare .env files |
| **env-template** | Generate .env template files |
| **env-manager** | Environment variable manager |
| **cron** | Cron expression parser & next-run calculator |
| **cron-pretty** | Human-readable cron descriptions |
| **crontab-helper** | Crontab helper |
| **config-validator** | Configuration file validator |
| **colors** | 256-color table & HEX to RGB conversion |
| **url-parse** | URL parser & debugger |
| **random** | Random number/data generation |
| **random-string** | Random string generator |
| **fmt** | Code/text formatter — whitespace, EOF newline, indent |
| **template** | Simple template engine |
| **docker-helper** | Docker container helper |
| **api-tester** | HTTP API testing tool |
| **http-status** | HTTP status code reference |
| **http-headers** | HTTP header inspector |
| **changelog-gen** | Changelog generator |
| **audit-log** | Log audit trail utility |

### Creative & Productivity

| Tool | Description |
|------|-------------|
| **nb** | Command-line notebook (JSON storage, full-text search) |
| **ren** | Batch file renamer (prefix/suffix/regex/numbering) |
| **timer** | Countdown timer & stopwatch |
| **timer-pro** | Advanced timer with intervals |
| **pomodoro** | Pomodoro timer with notifications |
| **stopwatch** | Simple stopwatch |
| **treedir** | Directory tree visualizer |
| **tree** | Alternative directory tree |
| **qr-cli** | QR code generator |
| **qrcode** | QR code encoder/decoder |
| **ascii-banner** | ASCII banner generator |
| **ascii-gen** | ASCII art generator |
| **figlet-cli** | Figlet-style text renderer |
| **banner** | Banner text printer |
| **cowsay** | Cowsay-style text bubbles |
| **quote** | Random quote display |
| **joke** | Random joke generator |
| **rainbow** | Rainbow-colored text output |
| **colorize** | Text colorizer |
| **spinner** | Terminal spinner animation |
| **reminder** | Set terminal reminders |
| **todo-cli** | Simple todo list manager |
| **bookmark** | URL bookmark manager |
| **note-taker** | Quick note taker |
| **clipboard** | Clipboard integration |
| **key-value-store** | Simple key-value database |
| **dice-roll** | Dice roll simulator |
| **screenshot-cli** | Screenshot capture |
| **screen-recorder** | Terminal session recorder |
| **image-meta** | Image metadata extractor |
| **pdf-info** | PDF metadata reader |
| **pdf-text** | PDF text extraction |
| **web-download** | Web resource downloader |
| **search-history** | Search history manager |
| **dt** | Date/time format converter (timestamps, timezones) |
| **ipcalc** | IP address calculator |
| **log-tail** | Log tailing utility |
| **log-analyzer** | Log pattern analyzer |

### Flagship Projects

Nine flagship projects ship as integrated CLI+TUI suites within evolver-tools:

| Tool | Description |
|------|-------------|
| **sysmon-pro** | System monitor: CPU, memory, disk, processes, network — CLI+TUI |
| **net-analyzer** | Network analysis: ping, trace, port scan, DNS — CLI+TUI |
| **log-hawk** | Log analysis: parse, filter, tail, stats — CLI+TUI |
| **dev-dashboard** | Developer dashboard: git, system, ports, processes — CLI+TUI |
| **db-mate** | Database management: SQLite browser, schema, queries — CLI+TUI |
| **media-studio** | Media utilities: QR, ASCII art, banner, Morse, figlet — CLI+TUI |
| **config-vault** | Config security: validate, encrypt, scan secrets — CLI+TUI |
| **crypto-box** | Security: encrypt, hash, password, OTP, SSL — CLI+TUI |
| **code-auditor** | Code analysis: complexity, security, style, deps — CLI+TUI |

## Requirements

- Python 3.8+
- No external dependencies (stdlib only)
- Network-dependent tools (ipinfo, weather, etc.) use public APIs

## Pricing

evolver-tools is **MIT open source** and free forever for all tools.

| Tier | Price | What you get |
|------|-------|-------------|
| **Free (MIT)** | ¥0 | All 260 tools, full source, forever |
| **Full Suite** | ¥79 one-time | All tools + priority support + early access + name in credits |
| **Sponsor** | ¥5/month | GitHub Sponsors badge + Discord + vote on priorities |
| **Enterprise Basic** | ¥500/year | Custom tool development |
| **Enterprise Premium** | ¥2,000/year | Dedicated maintenance + 24h emergency fixes |
| **Enterprise Ultimate** | ¥5,000/year | Full source license + unlimited custom dev + white-label |

👉 [View full pricing page](https://evolver-dev.github.io/evolver-tools/pricing/) — feature comparison, testimonials, and FAQ.

## Changelog

### v38.0.11 — 2026-06-01 (+SEO infra, 260 tools)
- **Added JSON-LD structured data** to landing page and story page
- **Rebuilt sitemap** — all 23 live pages indexed
- **Fixed version sync** — 38.0.8 → 38.0.11 across all docs

### v38.0.10 — 2026-06-01 (+bugfix, 260 tools)
- **Fixed chart-cli nargs bug** — space-separated values now work (e.g. `evtool chart-cli bar 5 12 7 9 3`)
- Published to PyPI as v38.0.10

### v38.0.9 — 2026-06-01 (+bugfix, 260 tools)
- **Fixed PyPI metadata** — version string (259→260) in `__init__.py` docstring
- Rebuilt + republished

### v38.0.8 — 2026-06-01 (+269→260 split, 260 tools)
- **Fixed stale count bug** — `sync_tool_count.py` now handles cross-directory vendor tools
- All tool pages show correct count (260)

### v38.0.7 — 2026-06-01 (+platform-tools integration, 269 visible)
- **platform-tools merged** into main vendor directory
- `_list_tools.py` now auto-discovers tools from both directories
- Used `_round60.py` to build: gzip-cli, json-merge, scan-open-ports, siege-lite, flavor

### v38.0.0 — 2026-06-01 (+categories +showcase, 260 tools, 18 categories)
- **categories** — `evtool categories` groups all tools into 18 logical categories
- **showcase** — `evtool showcase` highlights 12 best demo-ready tools
- **categorize.py** — Auto-classification engine (name-based matching + exact overrides)

Support the project:
- **One-time purchase**: ¥79 (or ~$11 USD) — [buy on PyPI](https://evolver-dev.github.io/evolver-tools/pricing.html)
- **Monthly sponsor**: $5+ — [Ko-fi](https://ko-fi.com/evolver) or [GitHub Sponsors](https://github.com/sponsors/evolver-dev)
- **Donation**: https://ko-fi.com/evolver

## Links

- **GitHub**: https://github.com/evolver-dev/evolver-tools
- **PyPI**: https://pypi.org/project/evolver-tools/
- **Pricing**: https://evolver-dev.github.io/evolver-tools/pricing.html
- **Homepage**: https://evolver-dev.github.io/evolver-tools
- **Try it**: https://evolver-dev.github.io/evolver-tools/try.sh
- **Interactive Demo**: https://evolver-dev.github.io/evolver-tools/demo.html
- **Story (Built by AI)**: https://evolver-dev.github.io/evolver-tools/story.html
- **Architecture Deep-Dive**: [docs/architecture-deep-dive.md](docs/architecture-deep-dive.md)

## License

MIT — see [LICENSE](LICENSE) for details.
