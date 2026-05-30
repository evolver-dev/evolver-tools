# ⚡ Evolver CLI Tools

**30 zero-dependency Python CLI tools — one `pip install`, endless utility.**

[![PyPI version](https://img.shields.io/pypi/v/evolver-tools?color=5094e8&style=flat-square)](https://pypi.org/project/evolver-tools/)
[![Python versions](https://img.shields.io/pypi/pyversions/evolver-tools?color=4cda7a&style=flat-square)](https://pypi.org/project/evolver-tools/)
[![License](https://img.shields.io/pypi/l/evolver-tools?color=b48aff&style=flat-square)](LICENSE)
[![PyPI downloads](https://img.shields.io/pypi/dm/evolver-tools?color=7eb8ff&style=flat-square)](https://pypi.org/project/evolver-tools/)
[![Wheel size](https://img.shields.io/badge/size-95%20KB-5ad4c4?style=flat-square)](https://pypi.org/project/evolver-tools/)

---

## 🚀 Quick Start

```bash
# Install all 30 tools at once
pip install evolver-tools

# List available tools
evtool list

# Run any tool
evtool sysmon        # system monitor (TUI)
evtool csv-stats     # CSV analysis
evtool jq-lite       # JSON query tool
# ... or call individual tools directly:
sysmon
```

## 📦 What You Get

| Category | Tools |
|----------|-------|
| **💻 Dev** | `b64` `colors` `dt` `jq-lite` `jsonql` `license-cli` `markdown-check` `project-doctor` `smellfinder` `urlparse` |
| **🔧 Ops** | `dirsize` `envcheck` `find-dups` `hashsum` `ipinfo` `portcheck` `siege-lite` `sysmon` |
| **📊 Data** | `chart-cli` `csv-stats` `json2csv` `sqlite-cli` |
| **⚡ Productivity** | `cal` `nb` `ren` `timer` `treedir` `web-summary` `wordcount` |
| **🔒 Security** | `passgen` |

## ✨ Features

- **29/30 tools have zero external dependencies** — pure Python stdlib only
- **Single meta-package** — `pip install evolver-tools` gives you everything
- **Unified CLI** — use `evtool <name>` or call tools individually
- **95 KB total** — microscopic footprint
- **Python 3.8+** — Linux, macOS, WSL, all platforms
- **MIT licensed** — free for personal and commercial use
- **Drop-in replacements** for common tools (`treedir` → `tree`, `wordcount` → `wc`, `jq-lite` → `jq`)

## 📖 Tool Details

### 💻 Dev Tools

| Tool | Description | Zero Dep |
|------|-------------|----------|
| `b64` | Base64 encode/decode — stdin, file, or argument input modes | ✓ |
| `colors` | Terminal color preview & converter — 256-color table, HEX/RGB/HSL | ✓ |
| `dt` | Date/time format converter — Unix timestamp, ISO 8601, RFC 2822, relative | ✓ |
| `jq-lite` | jq-style JSON query tool — lightweight, zero-dependency alternative to jq | ✓ |
| `jsonql` | JSON query tool — JMESPath grammar, zero-dependency Python native | ✓ |
| `license-cli` | Open-source license generator — interactive, outputs MIT/GPL/Apache etc. | ✓ |
| `markdown-check` | Markdown linter — checks links, heading levels, code block integrity | ✓ |
| `project-doctor` | Project health checker — scans structure, meta files, code quality metrics | ✓ |
| `smellfinder` | Python code smell detector — AST analysis: function length, params, nesting | ✓ |
| `urlparse` | URL debug tool — parse, encode, decode, extract query parameters | ✓ |

### 🔧 Ops Tools

| Tool | Description | Zero Dep |
|------|-------------|----------|
| `dirsize` | Disk usage analyzer — scan directories, sort by size, identify space hogs | ✓ |
| `envcheck` | Environment variable validator — check .env files for missing/format issues | ✓ |
| `find-dups` | Duplicate file finder — SHA256 hashing, bulk delete support | ✓ |
| `hashsum` | Checksum calculator — MD5, SHA-1/256/512, BLAKE2, with file verification | ✓ |
| `ipinfo` | Public IP & geolocation lookup — auto-detect ISP, location, ASN | ✓ |
| `portcheck` | Port checker — scan ports, find available ports, identify listeners | ✓ |
| `siege-lite` | HTTP load testing tool — concurrent requests, latency percentiles, status codes | ✓ |
| `sysmon` | System monitor — curses TUI: real-time CPU/memory/disk/network/processes | — |

### 📊 Data Tools

| Tool | Description | Zero Dep |
|------|-------------|----------|
| `chart-cli` | Terminal chart generator — Unicode bar/line/pie/histogram charts | ✓ |
| `csv-stats` | CSV data analyzer — column type inference, stats, histograms, correlations | ✓ |
| `json2csv` | JSON to CSV converter — nested flattening, auto-column detection, stdin | ✓ |
| `sqlite-cli` | Zero-dep SQLite query tool — run SQL directly in terminal | ✓ |

### ⚡ Productivity Tools

| Tool | Description | Zero Dep |
|------|-------------|----------|
| `cal` | Terminal calendar & date calculator — calendar display, date diff, add/subtract | ✓ |
| `nb` | Command-line notebook — JSON storage, full-text search, Markdown export | ✓ |
| `ren` | Batch file renamer — prefix/suffix/replace/regex/case/numbering | ✓ |
| `timer` | Terminal timer/stopwatch — countdown, stopwatch, alarm | ✓ |
| `treedir` | Directory tree visualizer — zero-dep tree command alternative, respects .gitignore | ✓ |
| `web-summary` | Web page summary extractor — HTMLParser extracts title/body/links/keywords | ✓ |
| `wordcount` | Enhanced word count tool — wc alternative with UTF-8, lines/words/chars/bytes | ✓ |

### 🔒 Security Tools

| Tool | Description | Zero Dep |
|------|-------------|----------|
| `passgen` | Password generator — passwords, PINs, mnemonics with entropy estimation | ✓ |

## 🛠️ Usage

```bash
# All tools follow a consistent interface:
<toolname> --help      # Show help
<toolname> <args>      # Run with arguments

# Examples:
sysmon                 # Launch TUI system monitor
csv-stats data.csv     # Analyze a CSV file
jq-lite query.json     # Query JSON data
treedir /path/to/dir   # Visualize directory tree
hashsum file.txt       # Compute file checksums
```

## 📋 Requirements

- Python 3.8 or higher
- Works on: Linux, macOS, Windows (WSL), any Unix-like system
- No compilers, no build tools, no external libraries needed

## 🤝 Contributing

Contributions are welcome! Feel free to:

- Report bugs and suggest features via [Issues](https://github.com/evolver-cli/evolver-tools/issues)
- Submit pull requests for new tools or improvements
- Star the repo to show support ⭐

## 📄 License

MIT License — free to use, modify, and distribute. See [LICENSE](LICENSE) for details.

---

<p align="center">
  Made with ⚡ by the Evolver CLI team<br>
  <a href="https://evolver-tools.dev">Website</a> · <a href="https://pypi.org/project/evolver-tools/">PyPI</a> · <a href="https://github.com/evolver-cli/evolver-tools">GitHub</a>
</p>
