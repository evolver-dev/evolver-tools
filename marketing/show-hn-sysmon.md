# Show HN: sysmon-pro — Real-time system monitor for your terminal (pure Python, 0 deps)

## Title (pick the best one)

A) Show HN: sysmon-pro – a real-time system monitor for the terminal (pure Python, 0 deps)
B) Show HN: I built htop in pure Python – sysmon-pro, zero dependencies
C) Show HN: sysmon-pro – 500 lines of stdlib Python that replaces htop/btop/glances

## Body

Hey HN!

I got tired of installing htop/btop/glances on every new server and dealing with missing dependencies, C compiler errors, or Python package conflicts. So I built sysmon-pro — a real-time system monitor that works everywhere Python 3 does.

```
pip install evolver-tools
evtool sysmon
```

What it does:
• Real-time CPU, memory, disk, and network monitoring
• Process list with search and kill support
• Full curses TUI with live updates
• JSON output mode for scripting/pipe
• GPU monitoring (NVIDIA)
• Alert thresholds with desktop notifications
• History logging to CSV
• Zero external dependencies (Python stdlib only!)

It's ~556 lines of MIT-licensed Python. No pip dependencies whatsoever. Works on Linux, macOS, and WSL.

This is part of the evolver-tools collection (122 tools, 9 flagship projects, all MIT):

```
evolver-tools on PyPI: https://pypi.org/project/evolver-tools/11.0.0/
GitHub: https://github.com/evolver-dev/evolver-tools
```

Would love your feedback — especially on what's the most painful CLI tool you reach for daily that could be done better in pure Python.

## Screenshot idea
Take a screenshot of `evtool sysmon` running in a terminal with CPU/memory bars visible.

===

Suggested posting time: Tuesday-Thursday, 13:00-15:00 UTC
Post to: https://news.ycombinator.com/submit
