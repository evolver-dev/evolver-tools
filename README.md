# EVOLVER Tools

**244 CLI tools + 9 flagship projects — one `pip install`.**

Zero-dependency (240/244), cross-platform, production-ready. Version **34.0.0**.
Systems ops, data processing, text manipulation, security, dev tooling, and creative utilities.
All in a single install — not 239 separate packages.

## Quick Start

```bash
pip install evolver-tools
evtool list             # Show all 244 tools
evtool sysmon           # Launch system monitor
evtool ff < data.txt    # Fuzzy search through data
evtool csv-stats data.csv  # Analyze CSV columns
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
- No external dependencies for 239 of 239 tools (stdlib only)
- Network-dependent tools (ipinfo, weather, etc.) use public APIs

## Pricing

evolver-tools is **MIT open source** and free forever for all tools.

| Tier | Price | What you get |
|------|-------|-------------|
| **Free (MIT)** | ¥0 | All 239 tools, full source, forever |
| **Full Suite** | ¥79 one-time | All tools + priority support + early access + name in credits |
| **Sponsor** | ¥5/month | GitHub Sponsors badge + Discord + vote on priorities |
| **Enterprise Basic** | ¥500/year | Custom tool development |
| **Enterprise Premium** | ¥2,000/year | Dedicated maintenance + 24h emergency fixes |
| **Enterprise Ultimate** | ¥5,000/year | Full source license + unlimited custom dev + white-label |

👉 [View full pricing page](https://evolver-dev.github.io/evolver-tools/pricing/) — feature comparison, testimonials, and FAQ.

Support the project via one-time purchase (¥79) or monthly sponsorship on [GitHub Sponsors](https://github.com/sponsors/evolver-dev).

## Links

- **GitHub**: https://github.com/evolver-dev/evolver-tools
- **PyPI**: https://pypi.org/project/evolver-tools/
- **Pricing**: https://evolver-dev.github.io/evolver-tools/pricing.html
- **Homepage**: https://evolver-dev.github.io/evolver-tools

## License

MIT — see [LICENSE](LICENSE) for details.
