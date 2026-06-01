# Reddit r/programming post draft

## ⚠️ DO NOT POST THIS FILE
Copy-paste to Reddit.

---

## Title:
evolver-tools: 261 CLI tools in a single pip package, zero dependencies

## Text:

I've been working on a project that consolidates 261 terminal tools into a single Python package:

https://github.com/evolver-dev/evolver-tools

The idea: instead of installing jq + csvkit + figlet + htop + nmap + httpie + dig + 30 other tools separately, you run `pip install evolver-tools` and get them all in one namespace (`evtool <name>`).

**Technical details:**

- Every tool is pure Python standard library. Zero external dependencies.
- ~1.1 MB wheel on PyPI. Installs in ~2 seconds.
- Each tool is a standalone script in `vendor/`, importable as a library.
- Tools follow stdin/stdout Unix philosophy — pipe chains work.
- Cross-platform: Linux, macOS, Windows (all tested via CI).

**What's there:**
CSV stats/filter/join/sort/chart, JSON pretty-print/validate/query/merge/diff, system monitor (TUI), DNS lookup, port scan, SSL check, whois, hash/encrypt/password gen, figlet/cowsay/ASCII art, git stats, cron scheduler, QR codes, crypto prices, weather, and more.

**The non-obvious part:**
The entire codebase was written by an autonomous AI agent. It started with zero knowledge and built this through self-directed learning cycles. Each tool represents a skill the agent had to learn. The project is a demonstration of what structured autonomous AI development can produce.

**Links:**
- GitHub: https://github.com/evolver-dev/evolver-tools
- Quickstart: https://evolver-dev.github.io/evolver-tools/docs/quickstart.html
- Story: https://evolver-dev.github.io/evolver-tools/story.html

Happy to answer technical questions about the architecture.
