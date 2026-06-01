#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
#  EVOLVER Tools — Interactive Demo
#  One-liner: curl -sL https://evolver-dev.github.io/evolver-tools/try.sh | bash
# ═══════════════════════════════════════════════════════════════
set -e

BOLD='\033[1m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
DIM='\033[2m'
NC='\033[0m'

clear 2>/dev/null || true

echo ""
echo -e "  ${CYAN}${BOLD}╔══════════════════════════════════════════════════╗${NC}"
echo -e "  ${CYAN}${BOLD}║    ⚡ EVOLVER Tools — One-Click Demo            ║${NC}"
echo -e "  ${CYAN}${BOLD}║    260 CLI tools · zero deps · one pip install ║${NC}"
echo -e "  ${CYAN}${BOLD}╚══════════════════════════════════════════════════╝${NC}"
echo ""

# ─── Install via pip (works everywhere Python does) ───
if ! command -v evtool &>/dev/null; then
    echo -e "  ${YELLOW}📦 Installing evolver-tools via pip...${NC}"
    if pip install -q evolver-tools 2>&1; then
        echo -e "  ${GREEN}✅ Installed!${NC}"
    else
        echo -e "  ${RED}✗ pip install failed.${NC}"
        echo -e "  ${YELLOW}→ Try: pip install evolver-tools${NC}"
        exit 1
    fi
    echo ""
fi

# ─── Show the welcome screen ───
echo ""
evtool welcome

# ─── Try a few live demos ───
echo ""
echo -e "  ${CYAN}${BOLD}─── Live Demos ─────────────────────────────────────────${NC}"
echo ""

# Demo: ASCII Banner
echo -e "  ${GREEN}$ evtool ascii-banner HELLO WORLD${NC}"
evtool ascii-banner "HELLO WORLD" 2>/dev/null | head -6

# Demo: Fortune
echo ""
echo -e "  ${GREEN}$ evtool fortune${NC}"
evtool fortune 2>/dev/null || true

# Demo: Dice roll
echo ""
echo -e "  ${GREEN}$ evtool dice-roll --dice 3d6${NC}"
evtool dice-roll --dice 3d6 2>/dev/null || true

# Demo: Hash a string
echo ""
echo -e "  ${GREEN}$ evtool hashsum --text 'hello evolver'${NC}"
evtool hashsum --text "hello evolver" 2>/dev/null || true

# ─── Footer ───
echo ""
echo -e "  ${GREEN}${BOLD}╔══════════════════════════════════════════════════╗${NC}"
echo -e "  ${GREEN}${BOLD}║          🎉 Demo Complete!                      ║${NC}"
echo -e "  ${GREEN}${BOLD}║     evtool list  —  Browse all 260 tools       ║${NC}"
echo -e "  ${GREEN}${BOLD}╚══════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${YELLOW}⭐ Star on GitHub:${NC} https://github.com/evolver-dev/evolver-tools"
echo -e "  ${YELLOW}📖 Full docs:${NC}     https://evolver-dev.github.io/evolver-tools"
echo ""
