# EVOLVER Tools

**36 essential CLI tools — one `pip install`.**

Zero-dependency (35/36), cross-platform, production-ready.
Monitor systems, analyze code, fuzzy-search data, query databases, and more.
104KB total — one install, not 32.

## Quick Start

```bash
pip install evolver-tools
evtool list             # Show all 32 tools
evtool ff < data.txt    # Fuzzy search through data
evtool sysmon           # Launch system monitor
evtool sqlite-cli my.db "SELECT * FROM users LIMIT 10"
```

## Tools

### Ops

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

### Developer

| Tool | Description |
|------|-------------|
| **smellfinder** | Python code smell detector (AST-based, 10+ patterns) |
| **project-doctor** | Project health checker (meta, structure, quality) |
| **license-cli** | Open-source license generator/validator |
| **markdown-check** | Markdown format validator & style checker |
| **sqlite-cli** | SQLite query tool — CSV/JSON/table output |
| **b64** | Base64 encode/decode with auto-detection |
| **jsonql** | Zero-dep JSON query tool (SQL-like syntax) |
| **jq-lite** | jq-style JSON query — filter, extract, transform |
| **urlparse** | URL parser & debugger |
| **colors** | 256-color table & HEX↔RGB conversion |

### Data & Analysis

| Tool | Description |
|------|-------------|
| **csv-stats** | CSV column analysis — histograms, frequencies, correlations |
| **json2csv** | JSON to CSV converter with nested key flattening |
| **chart-cli** | Terminal chart generator — bar, line, pie, histogram |
| **cal** | Calendar & date calculator |
| **web-summary** | Web page content extractor (title, body, links) |

### Productivity

| Tool | Description |
|------|-------------|
| **ff** | Interactive fuzzy finder (like fzf, pure Python curses TUI) |
| **nb** | Command-line notebook (JSON storage, full-text search) |
| **ren** | Batch file renamer (prefix/suffix/regex/numbering) |
| **timer** | Countdown timer & stopwatch with desktop notifications |
| **treedir** | Directory tree visualizer with depth control |
| **wordcount** | Enhanced word/char/line counter with language detection |
| **dt** | Date/time format converter (timestamps, timezones) |

### Security

| Tool | Description |
|------|-------------|
| **passgen** | Password generator with entropy display & charset rules |

## Requirements

- Python 3.8+
- No external dependencies (31 of 32 tools use stdlib only; ipinfo uses ip-api.com)

## License

MIT