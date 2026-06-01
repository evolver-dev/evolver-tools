# Show HN: evolver-tools — 276 CLI tools, zero dependencies, one pip install

**Title (suggested):**
Show HN: evolver-tools – 259 zero-dependency CLI tools, pip install one get 259

**URL:**
https://github.com/evolver-dev/evolver-tools

---

**Body draft (≈1800 chars — HN limit is 2000):**

I got tired of the "install 20 different packages from 5 different package managers" dance every time I set up a new machine. jq, csvkit, ripgrep, bat, httpie, fzf — each is great, but together they take minutes to install and some don't work on Windows.

So I built evolver-tools: one `pip install` gives you 276 CLI tools covering sysadmin, CSV/JSON/text processing, networking, crypto, math, encoding, devops, and more. Zero external dependencies. Works on Linux, macOS, and Windows.

```
pip install evolver-tools
evtool ascii-banner "Hello HN"   # Large ASCII art
evtool qrcode "https://hn.com"   # QR code in terminal
echo '5,12,8,20,3' | evtool chart-cli bar  # Bar chart
evtool sysmon                     # Live system monitor (curses TUI)
evtool search ssh                 # Fuzzy search all 276 tools
```

**How it works (the engineering bit):**

Each tool is a standalone Python file in vendor/ — no imports between them. The CLI runner auto-discovers them at import time using a filesystem scan + entry point registration. Every tool runs in a subprocess or inline depending on complexity, but NONE import anything outside the stdlib. The full dependency tree is: Python ≥3.8 and nothing else.

The package is 541KB on PyPI and every tool is a single `evtool <name> <args>` invocation. Tools use a consistent interface — positional args, flags with `--help`, pipe-friendly stdin/stdout.

**Why "259"?**

It's not a magic number — it's the count of standalone .py files in the vendor directory that the auto-registrar picks up. Some are tiny one-liners (hexdec, rot13), some are substantial (sysmon is a full curses dashboard, chart-cli draws bar/line/pie/radar charts, http-server is a static file server). I've been building them over the past month and the count grows naturally as I encounter needs.

**The honest tradeoffs:**

- Each individual tool is less polished than the dedicated tool. jq is way better than evtool jq-lite. But you get 259 for the cost of one install.
- The "zero dep" constraint means no syntax highlighting, no async, no binary wheels. Pure Python stdlib only.
- Some tools need network access (geo-ip, crypto-price, weather). They use urllib, which is stdlib.

**What's next:**

- More tools (I add 5-10/week based on what I need)
- Better Windows support (terminal color is tricky without ANSICON)
- A proper docs site is up at https://evolver-dev.github.io/evolver-tools/

The project is MIT licensed, free forever. Star if you find it useful: https://github.com/evolver-dev/evolver-tools

Would love feedback — what tools would you add?

---

**Best posting time:** Tuesday-Thursday, 9-11am ET for maximum HN visibility.

**Post tags:** #show #cli #python #devtools
