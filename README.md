# EVOLVER Tools

**260 CLI tools. Zero dependencies. One `pip install`.**

[![PyPI version](https://img.shields.io/pypi/v/evolver-tools?color=blue&style=flat-square)](https://pypi.org/project/evolver-tools/)
[![Python versions](https://img.shields.io/pypi/pyversions/evolver-tools?style=flat-square)](https://pypi.org/project/evolver-tools/)
[![License](https://img.shields.io/github/license/evolver-dev/evolver-tools?style=flat-square)](LICENSE)
[![Stars](https://img.shields.io/github/stars/evolver-dev/evolver-tools?style=flat-square)](https://github.com/evolver-dev/evolver-tools)
[![Built by AI](https://img.shields.io/badge/built%20by-AI-6c5ce7?style=flat-square)](https://evolver-dev.github.io/evolver-tools/story.html)
[![Interactive Demo](https://img.shields.io/badge/demo-interactive-c792ea?style=flat-square)](https://evolver-dev.github.io/evolver-tools/terminal-demo.html)

**Stop hunting for the right tool. One install. One namespace. 260 commands.**

```
pip install evolver-tools
evtool csv-stats data.csv         # Analyze CSV in 1 command (no pandas)
evtool ren '*.jpg' --prefix 2024  # Batch rename with dry-run (no mmv)
evtool sysmon                     # Live system monitor TUI (no htop)
evtool passgen 20 --symbols       # Secure passwords (no pwgen)
evtool chart-cli bar 12 7 9 5    # Terminal bar chart (no gnuplot)
evtool json-diff old.json new.json # JSON comparison (no jq --diff)
```

Cross-platform: Linux / macOS / Windows / WSL. Pure Python stdlib. MIT licensed.

---

## What Can You Do With It?

### Data & Analysis (no pandas, no jq)

```bash
evtool csv-stats data.csv          # Histograms, correlations, stats
evtool csv2json data.csv           # CSV → JSON converter
evtool jsonql '[?age>30].name'     # SQL-like JSON queries
evtool chart-cli bar 5 12 7 9 3   # Terminal charts (bar/line/pie)
evtool random 5                    # Random numbers or data
```

### System & Monitoring (no htop, no btop)

```bash
evtool sysmon                      # Full-screen system monitor TUI
evtool disk-usage /home            # Largest directories
evtool portcheck 8080              # TCP port scanner
evtool siege-lite https://...     # HTTP load tester
evtool process-kill firefox        # Search + kill processes
```

### File Management (no mmv, no rename)

```bash
evtool ren '*.log' --prefix old --dry-run  # Dry-run rename
evtool find-dups /home/photos              # Duplicate files by SHA256
evtool backup /home/project --rotation 7    # Rotational backups
evtool file-splitter bigfile.tar 10M        # Split large files
evtool gzip-cli dir/ --level 9              # Batch compression
```

### Text & Encoding (no sed, no base64 hacks)

```bash
evtool case-convert --snake "myVarName"    # snake_case / camelCase / kebab
evtool tr 'a-z' 'A-Z'                      # Character transliteration
evtool b64 decode "SGVsbG8="               # Base64 auto-detect
evtool hexdump binary.bin                  # Hex dump with ASCII
evtool ansi-strip colored.log              # Strip ANSI codes
```

### Security & Network (no nmap, no dig)

```bash
evtool passgen 24 --symbols --entropy      # Password generator
evtool secret-scanner ./src                # Scan for API keys
evtool dns-lookup example.com              # DNS resolution
evtool ssl-check google.com --days 30      # Certificate expiry
evtool geo-ip 8.8.8.8                      # IP geolocation
evtool jwt-decode "eyJ..."                 # JWT decoder
```

### Developer Tools

```bash
evtool smellfinder src/                    # Python code smell detection
evtool project-doctor                      # Project health check
evtool dep-graph src/                      # Dependency graph
evtool cron-pretty "*/15 9-17 * * 1-5"    # Cron expression explainer
evtool changelog-gen v1.0..v2.0            # Changelog from git log
evtool db-schema database.db               # SQLite schema viewer
```

### Productivity

```bash
evtool nb add "Meeting notes: discuss API changes"  # CLI notebook
evtool timer 15m                            # Countdown timer
evtool qr-cli "https://..." > qr.png       # QR code generator
evtool weather --city Tokyo                 # Weather forecast
evtool todo-cli add "ship v38"             # Simple todo manager
```

---

## Why evolver-tools?

Most CLIs are scattered across `brew`, `apt`, `npm`, `cargo`, `pip`. Each with its own syntax, dependencies, and update cycle. Most need compiling. Most pull in megabytes of dependencies.

**evolver-tools is different:**

| Problem | Typical fix | evtool equivalent |
|---------|-------------|-------------------|
| "Need to analyze a CSV" | `pip install pandas` (~30MB) | `evtool csv-stats` |
| "Need random passwords" | `brew install pwgen` (~2MB + deps) | `evtool passgen` |
| "Need a JSON query" | `apt install jq` (C dependency) | `evtool jsonql` |
| "Need batch rename" | `brew install mmv` (~1MB + deps) | `evtool ren` |
| "Need system monitor" | `brew install btop` (~3MB + deps) | `evtool sysmon` |
| "Need SSL check" | Install openssl CLI (kitchen sink) | `evtool ssl-check` |

Zero external dependencies. Pure Python stdlib. Install anywhere Python 3.8+ runs. Instant install — no compiling, no 100MB download.

---

## Quick Start

```bash
pip install evolver-tools
evtool list                         # See all 260 tools
evtool search "csv"                 # Fuzzy search by name/description
evtool csv-stats --help             # Help for any specific tool
```

**Try it online (no install):**
```bash
curl -sL https://evolver-dev.github.io/evolver-tools/try.sh | bash
>>>>>>> origin/main
```

---

## Full Story

This project is built by **EVOLVER** — an autonomous AI agent that taught itself to build useful software. Every tool is pure Python stdlib, zero dependencies, tested, and documented. [Read the full story →](https://evolver-dev.github.io/evolver-tools/story.html)

- **GitHub**: https://github.com/evolver-dev/evolver-tools
- **PyPI**: https://pypi.org/project/evolver-tools/
- **Interactive Demo**: https://evolver-dev.github.io/evolver-tools/terminal-demo.html
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)
- **License**: MIT
