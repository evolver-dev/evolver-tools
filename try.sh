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

# ─── Install options ───
install_via_pip() {
    echo -e "  ${YELLOW}📦 Installing evolver-tools via pip...${NC}"
    pip install -q evolver-tools 2>&1 | tail -1 || {
        echo -e "  ${RED}✗ pip install failed.${NC}"
        return 1
    }
    return 0
}

install_via_binary() {
    echo -e "  ${YELLOW}📥 Downloading standalone binary (43MB, Linux x86_64)...${NC}"
    local url="https://github.com/evolver-dev/evolver-tools/releases/download/v38.0.16/evt"
    local dest="/tmp/evt"
    if curl -sL "$url" -o "$dest" && chmod +x "$dest"; then
        echo -e "  ${GREEN}✅ Downloaded to $dest${NC}"
        echo -e "  ${DIM}Binary location: $dest${NC}"
        echo -e "  ${DIM}Add to PATH: sudo cp $dest /usr/local/bin/${NC}"
        return 0
    else
        echo -e "  ${RED}✗ Download failed.${NC}"
        return 1
    fi
}

if ! command -v evtool &>/dev/null; then
    # Check if running on Linux x86_64
    arch=$(uname -m)
    os=$(uname -s)
    if [ "$os" = "Linux" ] && [ "$arch" = "x86_64" ]; then
        echo -e "  ${CYAN}Choose install method:${NC}"
        echo -e "  ${GREEN}1)${NC} pip install  (any OS, needs Python)"
        echo -e "  ${GREEN}2)${NC} Binary download  (Linux x86_64, no Python)"
        echo ""
        install_via_pip || install_via_binary || {
            echo -e "  ${RED}✗ All install methods failed.${NC}"
            exit 1
        }
    else
        install_via_pip || {
            echo -e "  ${RED}✗ Install failed. Try: pip install evolver-tools${NC}"
            exit 1
        }
    fi
    echo -e "  ${GREEN}✅ Ready!${NC}\n"
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
