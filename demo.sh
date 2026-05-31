#!/usr/bin/env bash
# EVOLVER Tools — 30-Second Demo
# Run: bash demo.sh
# Or: chmod +x demo.sh && ./demo.sh
#
# Showcases 10 tools from the evolver-tools suite.
# Requires: pip install evolver-tools

set -e

DEMO=${1:-full}

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   EVOLVER Tools — Interactive Demo          ║"
echo "║   272+ tools · zero deps · one pip install  ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

sleep 0.5

# ─── 1. ASCII Banner ───
echo "─────────────────────────────────────────────"
echo "  [1/8] ascii-banner — Large ASCII art"
echo "─────────────────────────────────────────────"
evtool ascii-banner "EVOLVER"
echo ""
sleep 1

# ─── 2. Rainbow Text ───
echo "─────────────────────────────────────────────"
echo "  [2/8] rainbow — Colorful text output"
echo "─────────────────────────────────────────────"
evtool rainbow "272 CLI tools, zero dependencies, one pip install"
echo ""
sleep 0.8

# ─── 3. Cowsay ───
echo "─────────────────────────────────────────────"
echo "  [3/8] cowsay — Talking ASCII cow"
echo "─────────────────────────────────────────────"
evtool cowsay "I'm a CLI tool. Install me with: pip install evolver-tools"
echo ""
sleep 0.8

# ─── 4. QR Code ───
echo "─────────────────────────────────────────────"
echo "  [4/8] qrcode — QR code generator"
echo "─────────────────────────────────────────────"
evtool qrcode "https://github.com/evolver-dev/evolver-tools"
echo ""
sleep 0.8

# ─── 5. Bar Chart ───
echo "─────────────────────────────────────────────"
echo "  [5/8] chart-cli — Terminal bar chart"
echo "─────────────────────────────────────────────"
echo '120,85,200,45,160,95,210' | evtool chart-cli bar -w 30
echo ""
sleep 0.8

# ─── 6. Weather ───
echo "─────────────────────────────────────────────"
echo "  [6/8] weather-cli — Live weather (wttr.in)"
echo "─────────────────────────────────────────────"
evtool weather-cli Beijing 2>/dev/null | head -7
echo ""
sleep 0.8

# ─── 7. Emoji ───
echo "─────────────────────────────────────────────"
echo "  [7/8] emoji-cli — Search and display emoji"
echo "─────────────────────────────────────────────"
evtool emoji-cli rocket
evtool emoji-cli fire
evtool emoji-cli star
echo ""
sleep 0.8

# ─── 8. Crypto Price ───
echo "─────────────────────────────────────────────"
echo "  [8/8] crypto-price — Live crypto ticker"
echo "─────────────────────────────────────────────"
evtool crypto-price --coin bitcoin 2>/dev/null || echo "(offline — run when connected)"
echo ""
sleep 0.5

# ─── Done ───
echo "╔══════════════════════════════════════════════╗"
echo "║   Demo Complete!                             ║"
echo "║                                              ║"
echo "║   Next steps:                                ║"
echo "║   • evtool categories  — browse all 18 cats  ║"
echo "║   • evtool showcase   — 12 featured tools   ║"
echo "║   • evtool list       — full 272+ listing   ║"
echo "║   • evtool <tool> -h  — per-tool help       ║"
echo "║                                              ║"
echo "║   github.com/evolver-dev/evolver-tools       ║"
echo "╚══════════════════════════════════════════════╝"
