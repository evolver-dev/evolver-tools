# EVOLVER Tools

[![PyPI version](https://img.shields.io/pypi/v/evolver-tools?color=blue&style=flat-square)](https://pypi.org/project/evolver-tools/)
[![Python versions](https://img.shields.io/pypi/pyversions/evolver-tools?style=flat-square)](https://pypi.org/project/evolver-tools/)
[![PyPI downloads](https://img.shields.io/pypi/dm/evolver-tools?style=flat-square)](https://pypi.org/project/evolver-tools/)
[![License](https://img.shields.io/github/license/evolver-dev/evolver-tools?style=flat-square)](LICENSE)
[![Stars](https://img.shields.io/github/stars/evolver-dev/evolver-tools?style=flat-square)](https://github.com/evolver-dev/evolver-tools)

**254 CLI tools — one `pip install`, zero dependencies, all platforms.**

Stop hunting for packages. `pip install evolver-tools` gives you 254 tools — sysadmin, CSV, JSON, text, encoding, networking, math, and more. Everything ready to use as `evtool <name>`.

Zero external dependencies. Cross-platform (Linux / macOS / Windows). Version **38.0.0**.

> [`jq`](https://github.com/jqlang/jq) for JSON, [`csvkit`](https://github.com/wireservice/csvkit) for CSV, [`ripgrep`](https://github.com/BurntSushi/ripgrep) for search, [`nmap`](https://nmap.org/) for ports, [`httpie`](https://github.com/httpie/cli) for HTTP — each is best-in-class. But installing 20 of them takes minutes, requires multiple package managers (`brew`, `apt`, `cargo`, `npm`, `pip`), and some don't work on Windows.  
**evolver-tools** bundles 254 essential tools in one install. One interface. One `pip install`. Works everywhere.

## 30-Second Preview

```bash
pip install evolver-tools
evtool ascii-banner "EVOLVER"          # Large ASCII art banner
evtool rainbow "254 tools in 1 pip"    # Rainbow-colored text
evtool qrcode "https://evolver.dev"    # QR code generator
evtool cowsay "Zero deps!"             # Talking ASCII cow
echo '5,12,8,20,3,15' | evtool chart-cli bar   # Bar chart
evtool weather-cli Tokyo               # Live weather forecast
evtool emoji-cli rocket                # Search emoji
```

Or run the full interactive demo:
```bash
pip install evolver-tools
bash <(curl -s https://raw.githubusercontent.com/evolver-dev/evolver-tools/main/demo.sh)
```

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
| **Free (MIT)** | ¥0 | All 254 tools, full source, forever |
| **Full Suite** | ¥79 one-time | All tools + priority support + early access + name in credits |
| **Sponsor** | ¥5/month | GitHub Sponsors badge + Discord + vote on priorities |
| **Enterprise Basic** | ¥500/year | Custom tool development |
| **Enterprise Premium** | ¥2,000/year | Dedicated maintenance + 24h emergency fixes |
| **Enterprise Ultimate** | ¥5,000/year | Full source license + unlimited custom dev + white-label |

👉 [View full pricing page](https://evolver-dev.github.io/evolver-tools/pricing/) — feature comparison, testimonials, and FAQ.

## Changelog

### v38.0.0 — 2026-06-01 (+categories +showcase, 254 tools, 18 categories)
- **categories** — `evtool categories` groups all tools into 18 logical categories
- **showcase** — `evtool showcase` highlights 12 best demo-ready tools
- **categorize.py** — Auto-classification engine (name-based matching + exact overrides)

### v37.0.0 — 2026-06-01 (+5 tools, 254 total)
- **git-ignore** — Generate .gitignore templates (Python/Node/Go/Rust/Java/Docker/More)
- **mime-type** — Detect MIME type by file extension or magic bytes
- **color-convert** — Convert between HEX, RGB, HSL, HSV, CMYK, ANSI
- **csv-concat** — Concatenate multiple CSV files (same columns, header-preserving)
- **ansi-to-html** — Convert ANSI-colored terminal output to styled HTML

### v36.0.0 — 2026-06-01 (+5 tools, 254 total)
- **merge-json** — Deep merge multiple JSON files (arrays concatenate, dicts recurse)
- **validate** — Generic file validator (JSON/YAML/CSV/TOML/XML auto-detect)
- **diff-lines** — Line-by-line diff between two files (color, side-by-side)
- **csv-schema** — Infer CSV schema (column types, nulls, stats, samples)
- **chrono** — Advanced date/time calculator (durations, workdays, ranges, age)

### v34.0.0 — 2026-06-01 (+5 tools, 244 total)
- **emoji-cli** — Search and display emoji (230+ emoji, categories, --random)
- **html-strip** — Strip HTML tags, extract plain text (stdin/file, --preserve-links)
- **json-patch** — Apply JSON Patch (RFC 6902) operations to JSON files
- **markdown-format** — Format/beautify Markdown tables and lists
- **ansi-to-txt** — Strip ANSI escape codes, convert to plain text

Support the project via one-time purchase (¥79) or monthly sponsorship on [GitHub Sponsors](https://github.com/sponsors/evolver-dev).

## Links

- **GitHub**: https://github.com/evolver-dev/evolver-tools
- **PyPI**: https://pypi.org/project/evolver-tools/
- **Pricing**: https://evolver-dev.github.io/evolver-tools/pricing.html
- **Homepage**: https://evolver-dev.github.io/evolver-tools
- **Architecture Deep-Dive**: [docs/architecture-deep-dive.md](docs/architecture-deep-dive.md) — technical article on how 254 zero-dependency CLI tools are built

## License

MIT — see [LICENSE](LICENSE) for details.
