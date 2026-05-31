# Show HN: evolver-tools — 238 CLI Tools, One pip Install, Zero Dependencies

## Title (up to 80 chars):
Show HN: evolver-tools — 238 CLI tools, one pip install

## Post Body:

I built a single package that bundles **238 CLI tools** covering everything from system monitoring to CSV analysis to security scanning. One `pip install`, zero dependencies.

```
pip install evolver-tools
evtool sysmon          # TUI system monitor (CPU/mem/disk/net)
evtool csv-stats data.csv  # Analyze any CSV
evtool port-scan example.com  # Scan open ports
evtool diff-csv a.csv b.csv  # Diff two CSVs
evtool qr "hello"     # Generate QR codes
evtool siege-lite example.com  # HTTP load test
evtool code-auditor   # Static code analysis
evtool db-mate        # Database management
evtool chart data.json  # Terminal charts
evtool ff < data.txt  # Fuzzy search
```

**Why I built this:**
I got tired of hunting for the right CLI tool — `jq` for JSON, `csvkit` for CSV, `nmap` for ports, `httpie` for HTTP, `pyfiglet` for banners... they all have different syntaxes, different install methods, and break on different OSes.

So I put everything in one package with a unified `evtool` interface. Every tool follows the same pattern: `evtool <name> [args]`.

**Current scope:**
- 238 CLI tools across 6 categories
- 235/238 have zero dependencies (pure Python stdlib)
- 9 flagship projects with TUI/GUI modes
- ~17,200 lines of code
- MIT license, fully open source
- Cross-platform (Linux, macOS, Windows)

**Some highlights:**
- `evtool sysmon` — curses-based real-time system monitor
- `evtool csv-stats` — CSV column analyzer with histograms/frequencies/correlations
- `evtool db-mate` — SQLite/MySQL/PostgreSQL management from terminal
- `evtool code-auditor` — AST-based Python code smell detector
- `evtool dev-dashboard` — Developer dashboard with git status/tests/todos
- `evtool siege-lite` — HTTP load tester with latency percentiles
- `evtool chart` — Terminal charts (bar/line/pie/histogram)

**Would love feedback on:**
1. Which categories should I expand next?
2. Would you pay for a tool like this? (I priced it at ¥79 ~ $11)
3. Any killer tools I'm missing?

GitHub: https://github.com/evolver-dev/evolver-tools
PyPI: https://pypi.org/project/evolver-tools/

MIT — all free, always.
