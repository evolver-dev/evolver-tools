# EVOLVER Tools

**50 essential CLI tools — one `pip install`.**

Zero-dependency (49/50), cross-platform, production-ready.
Systems ops, data processing, dev tools, security, and creativity.
~170KB total — one install, not 50.

## Quick Start

```bash
pip install evolver-tools
evtool list             # Show all 50 tools
evtool ff < data.txt    # Fuzzy search through data
evtool sysmon           # Launch system monitor
evtool sort -n data.txt # Numeric sort
```

## Tools

### Ops

| Tool | Description | Selling point |
|------|-------------|---------------|
| **sysmon** | Real-time system monitor (curses TUI — CPU/mem/disk/net/processes) | See your server breathe |
| **dirsize** | Recursive directory space analyzer | Find what's eating your disk |
| **envcheck** | Environment variable validator (missing keys, formats) | Stop .env typos from breaking prod |
| **portcheck** | TCP port scanner & service detection | Port open? Service running? |
| **siege-lite** | HTTP load tester (concurrency, latency percentile) | How many req/s can your app handle? |
| **http-live** | SSE hot-reload HTTP server for development | Edit code, see changes. No refresh. |
| **ipinfo** | Public IP & geolocation lookup | Where's this server? |
| **hashsum** | File hash verification (MD5/SHA-1/256/512/BLAKE2, auto-detect) | Verify downloads in one command |
| **find-dups** | Find duplicate files by SHA256 hash, size, or name | Reclaim gigabytes |

### Developer

| Tool | Description | Selling point |
|------|-------------|---------------|
| **smellfinder** | Python code smell detector (AST-based, 10+ patterns) | Lint without pip install pylint |
| **project-doctor** | Project health checker (meta, structure, quality) | Project checkup in one command |
| **license-cli** | Open-source license generator/validator | License your repo instantly |
| **markdown-check** | Markdown format validator & style checker | Docs that don't embarrass you |
| **sqlite-cli** | SQLite query tool — CSV/JSON/table output | Query .db files without a GUI |
| **b64** | Base64 encode/decode with auto-detection | Paste, pipe, done |
| **jsonql** | Zero-dep JSON query tool (SQL-like syntax) | `jsonql "SELECT name FROM data WHERE age > 18"` |
| **jq-lite** | jq-style JSON query — filter, extract, transform | jq without installing jq |
| **urlparse** | URL parser & debugger | What's in that URL? |
| **colors** | 256-color table & HEX↔RGB conversion | Design that terminal theme |
| **fmt** | Code/text formatter — trailing whitespace, EOF newline, indent | Clean files, one command |

### Data & Analysis

| Tool | Description | Selling point |
|------|-------------|---------------|
| **csv-stats** | CSV column analysis — histograms, frequencies, correlations | Understand your CSV in seconds |
| **json2csv** | JSON to CSV converter with nested key flattening | API response → spreadsheet |
| **chart-cli** | Terminal chart generator — bar, line, pie, histogram | Charts without leaving the terminal |
| **cal** | Calendar & date calculator | What day is 45 days from now? |
| **web-summary** | Web page content extractor (title, body, links) | Read the web from your terminal |
| **yaml2json** | Convert YAML to JSON (zero dependencies, basic YAML subset) | Config files \u2192 pipeable JSON |
| **sort** | Line sorting — alpha, numeric, reverse, unique, by column | Sort data without `sort(1)` |

### Productivity

| Tool | Description | Selling point |
|------|-------------|---------------|
| **ff** | Interactive fuzzy finder (fzf, pure Python curses TUI) | Search files, history, anything |
| **nb** | Command-line notebook (JSON storage, full-text search) | Notes in your terminal |
| **ren** | Batch file renamer (prefix/suffix/regex/numbering) | Rename 100 files in one command |
| **timer** | Countdown timer & stopwatch with desktop notifications | Pomodoro in your terminal |
| **treedir** | Directory tree visualizer with depth control | `tree` on every OS |
| **wordcount** | Enhanced word/char/line counter with language detection | wc on steroids |
| **dt** | Date/time format converter (timestamps, timezones) | `dt 1735689600` → human date |

### Security

| Tool | Description | Selling point |
|------|-------------|---------------|
| **passgen** | Password generator with entropy display & charset rules | Generate passwords that don't suck |
| **uuid** | UUID generator (v1/v3/v4/v5/v7) | v4, v7, any UUID in one command |
| **cron** | Cron expression parser & next-run calculator | "What does 0 2 * * 1 actually run?" |

## Requirements

- Python 3.8+
- No external dependencies (38 of 39 tools use stdlib only; ipinfo hits ip-api.com)

## Pricing

evolver-tools is **MIT open source** — free for everyone, forever.

| Tier | Price | What you get |
|------|-------|-------------|
| **Free (MIT)** | ¥0 | All 167 tools, full source, forever |
| **Full Suite** | ¥79 one-time | All tools + priority support + early access + name in credits |
| **Sponsor** | ¥5/month | GitHub Sponsors badge + Discord + vote on priorities |
| **Enterprise Basic** | ¥500/year | Custom tool development |
| **Enterprise Premium** | ¥2,000/year | Dedicated maintenance + 24h emergency fixes |
| **Enterprise Ultimate** | ¥5,000/year | Full source license + unlimited custom dev + white-label |

👉 **[View full pricing page](https://evolver-dev.github.io/evolver-tools/pricing/)** — includes feature comparison table, testimonials, and FAQ.

Support the project via one-time purchase (¥79) or monthly sponsorship on [GitHub Sponsors](https://github.com/sponsors/evolver-dev).

## License

MIT
