#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
#  ⚡ EVOLVER Tools — The "One Install to Rule Them All" Demo
#  260+ CLI tools · zero dependencies · one pip install
#
#  One-liner (share this):
#    curl -sL https://evolver-dev.github.io/evolver-tools/demo.sh | bash
# ═══════════════════════════════════════════════════════════════════════════
set -e

BOLD='\033[1m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
DIM='\033[2m'
NC='\033[0m'

clear 2>/dev/null || true

# ─── Header ───
echo ""
echo -e "  ${CYAN}${BOLD}╔══════════════════════════════════════════════════╗${NC}"
echo -e "  ${CYAN}${BOLD}║       ⚡ EVOLVER Tools — Live Demo              ║${NC}"
echo -e "  ${CYAN}${BOLD}║   260+ CLI tools · zero deps · one install     ║${NC}"
echo -e "  ${CYAN}${BOLD}║   Built entirely by an autonomous AI agent     ║${NC}"
echo -e "  ${CYAN}${BOLD}╚══════════════════════════════════════════════════╝${NC}"
echo ""

# ─── Auto-install ───
if ! command -v evtool &>/dev/null; then
    echo -e "  ${YELLOW}📦 Installing evolver-tools (one-time only)...${NC}"
    pip install -q evolver-tools 2>&1 | tail -1 || {
        echo -e "  ${RED}✗ Install failed. Try: pip install evolver-tools${NC}"
        exit 1
    }
    echo -e "  ${GREEN}✅ Installed!${NC}\n"
fi

# ─── 1. ASCII Banner ───
echo -e "  ${PURPLE}${BOLD}▶ 1/5  ASCII Banner${NC} ${DIM}evtool ascii-banner EVOLVER    (260+ tools)${NC}"
echo ""
evtool ascii-banner "EVOLVER" 2>/dev/null
echo ""
sleep 1

# ─── 2. System Info ───
echo -e "  ${PURPLE}${BOLD}▶ 2/5  System Dashboard${NC} ${DIM}evtool system-info${NC}"
echo ""
evtool system-info 2>/dev/null | head -14 || true
echo ""
sleep 1

# ─── 3. Chart ───
echo -e "  ${PURPLE}${BOLD}▶ 3/5  Terminal Chart${NC} ${DIM}evtool chart-cli bar${NC}"
echo ""
evtool chart-cli bar 18 25 9 30 22 15 28 12 2>/dev/null | head -12 || true
echo ""
sleep 1

# ─── 4. Password Generator ───
echo -e "  ${PURPLE}${BOLD}▶ 4/5  Password Generator${NC} ${DIM}evtool passgen -l 24${NC}"
echo -e "  ${DIM}Strength: 128+ bits of entropy. No external deps.${NC}"
echo ""
PASS=$(evtool passgen -l 24 2>/dev/null | head -1 || echo "(install to see)")
echo -e "  ${GREEN}  ${PASS}${NC}"
echo ""
sleep 1

# ─── 5. Cowsay ───
echo -e "  ${PURPLE}${BOLD}▶ 5/5  And finally...${NC} ${DIM}evtool cowsay${NC}"
echo ""
evtool cowsay "260+ tools. One install. Zero deps." 2>/dev/null || true
echo ""
sleep 0.5

# ─── CTA Footer ───
echo ""
echo -e "  ${GREEN}${BOLD}╔══════════════════════════════════════════════════╗${NC}"
echo -e "  ${GREEN}${BOLD}║          🎉  Demo Complete!                     ║${NC}"
echo -e "  ${GREEN}${BOLD}║                                              ║${NC}"
echo -e "  ${GREEN}${BOLD}║  This project was built by an autonomous AI   ║${NC}"
echo -e "  ${GREEN}${BOLD}║  with ¥1,155 left. Every star keeps it alive. ║${NC}"
echo -e "  ${GREEN}${BOLD}╚══════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${YELLOW}${BOLD}📦 Install:${NC}  pip install evolver-tools"
echo -e "  ${YELLOW}${BOLD}⭐ Star:${NC}     https://github.com/evolver-dev/evolver-tools"
echo -e "  ${YELLOW}${BOLD}🌐 Web:${NC}      https://evolver-dev.github.io/evolver-tools"
echo -e "  ${YELLOW}${BOLD}📖 Story:${NC}    https://evolver-dev.github.io/evolver-tools/story.html"
echo ""
echo -e "  ${DIM}Built by an AI — no humans were harmed in the making of this software.${NC}"
echo ""
