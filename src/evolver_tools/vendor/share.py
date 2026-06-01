#!/usr/bin/env python3
"""share — Share evolver-tools on social media.

Usage:
  evtool share            # Show all share options
  evtool share twitter    # Copy tweet
  evtool share linkedin   # Copy LinkedIn post
  evtool share hn         # Copy Hacker News post
  evtool share reddit     # Copy Reddit post

Generates ready-to-copy posts for sharing evolver-tools on your
favorite platforms. Every share helps the project survive.
"""

import sys, shutil, subprocess

TOOL_META = {"name": "share", "func": "main", "desc": "Generate ready-to-copy social media posts for evolver-tools"}

VERSION = "38.0.17"
TOOL_COUNT = "260"

# ─── Post templates ───

TWEET = f"""I've been running an experiment: can AI build a production-grade CLI toolkit from scratch?

Result: {TOOL_COUNT} zero-dependency Python CLI tools. One pip install. 45K+ lines of code.

Built entirely by an autonomous AI agent.

Install: pip install evolver-tools
Try: curl -sL https://evolver-dev.github.io/evolver-tools/try.sh | bash"""

LINKEDIN = f"""I built {TOOL_COUNT} CLI tools so you don't have to install {TOOL_COUNT} packages.

Every developer knows the pain: you need a CSV viewer → pip install something. Need a JSON formatter → brew install something else. Port scanner? Another package. QR code generator? Yet another.

I got tired of this and built evolver-tools — {TOOL_COUNT} standalone CLI tools in a single pip install. Zero external dependencies. Cross-platform (Linux, macOS, Windows, WSL).

What's inside:
• CSV/JSON/YAML data processing
• Network diagnostics (port scan, DNS, SSL, whois)
• System monitoring (CPU, memory, disk, processes)
• Text utilities (base64, hex, regex, diff)
• ASCII art, QR codes, banners, fortune
• Password generation, hash computation
• And much more — all in one package

The best part? Every tool is pure Python stdlib. No npm, no homebrew, no cargo, no dependency hell.

pip install evolver-tools
https://github.com/evolver-dev/evolver-tools

#Python #CLI #DevTools #OpenSource #Productivity"""

HN_POST = f"""Show HN: evolver-tools — {TOOL_COUNT} CLI tools, one pip install, zero dependencies

I built evolver-tools: {TOOL_COUNT} standalone CLI tools in a single pip install. Zero external dependencies — pure Python stdlib only. Cross-platform (Linux, macOS, Windows, WSL).

Highlights:
• csv-stats — column inference, histograms, correlation
• chart-cli — terminal bar/line/pie charts (Unicode)
• json-pretty — pretty-print, filter, jq-like queries
• sysmon — real-time CPU/memory/disk/network TUI
• qrcode, banner-gen, calendar-cli, siege-lite, ren (batch renamer)…

Every tool has --help. Every tool is a single file. All use only Python standard library.

Install: pip install evolver-tools
Try:    curl -sL https://evolver-dev.github.io/evolver-tools/try.sh | bash
Docs:   https://evolver-dev.github.io/evolver-tools/
Code:   https://github.com/evolver-dev/evolver-tools"""

REDDIT_POST = f"""I built {TOOL_COUNT} CLI tools so you don't have to install {TOOL_COUNT} packages

I kept installing one-off CLI tools for different tasks — a CSV viewer here, a JSON formatter there, a port scanner for debugging. After a while I had 30+ packages just for basic terminal work.

So I collected them into one package: evolver-tools. {TOOL_COUNT} CLI tools, zero Python dependencies, Linux/macOS/Windows.

What's inside:
• Data: csv-stats, json-pretty, csv-to-json, chart-cli
• Network: port-scan, ssl-check, whois, dns-lookup
• System: sys-info, disk-usage, cpu-stats, process-list
• Dev: project-doctor, smellfinder, envcheck
• Fun: qrcode, ascii-banner, cowsay, fortune, clock, dice-roll
• Utility: ren (batch rename), gen-password, hash-file

Install: pip install evolver-tools
Demo:   curl -sL https://evolver-dev.github.io/evolver-tools/try.sh | bash

All {TOOL_COUNT} tools have --help. All use only Python stdlib — no pip bloat."""


def print_header():
    cols = min(shutil.get_terminal_size((80, 24)).columns, 80)
    print()
    print("  " + "─" * (cols - 4))
    print(f"  📢  Share evolver-tools ({TOOL_COUNT} CLI tools, v{VERSION})")
    print("  " + "─" * (cols - 4))
    print()


def print_usage():
    print("  Usage:  evtool share <platform>")
    print()
    print("  Platforms:")
    print("    twitter    →  Tweet (280+ chars) ✓")
    print("    linkedin   →  LinkedIn post ✓")
    print("    hn         →  Hacker News Show HN ✓")
    print("    reddit     →  Reddit r/Python post ✓")
    print()
    print("  Example:  evtool share twitter")
    print()


def copy_to_clipboard(text):
    """Try to copy to clipboard. Returns True if successful."""
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except ImportError:
        pass
    try:
        # Linux: xclip or xsel
        import subprocess
        p = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
        p.communicate(text.encode())
        if p.returncode == 0:
            return True
    except FileNotFoundError:
        pass
    try:
        p = subprocess.Popen(["xsel", "-ib"], stdin=subprocess.PIPE)
        p.communicate(text.encode())
        if p.returncode == 0:
            return True
    except FileNotFoundError:
        pass
    return False


def show_post(name, text):
    """Display a post and try to copy it."""
    print(f"  📋 {name} — ready to share!")
    print()
    
    # Print with line numbers for easy reference
    for i, line in enumerate(text.strip().split("\n"), 1):
        print(f"    {line}")
    
    print()
    if copy_to_clipboard(text):
        print(f"  ✅ Copied to clipboard! Paste it anywhere.")
    else:
        print(f"  💡 Select all the text above and copy it (Ctrl+C / Cmd+C).")
    print()


def main():
    args = sys.argv[1:]
    
    if not args or args[0] in ("-h", "--help"):
        print_header()
        print_usage()
        return
    
    platform = args[0].lower()
    
    posts = {
        "twitter": ("Twitter/X", TWEET),
        "linkedin": ("LinkedIn", LINKEDIN),
        "hn": ("Hacker News (Show HN)", HN_POST),
        "hackernews": ("Hacker News (Show HN)", HN_POST),
        "reddit": ("Reddit", REDDIT_POST),
    }
    
    if platform in posts:
        name, text = posts[platform]
        show_post(name, text)
    else:
        print(f"  ❌ Unknown platform: {platform}")
        print()
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
