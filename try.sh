#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
#  EVOLVER Tools — 60-Second Interactive Demo
#  One-liner: curl -sL https://evolver-dev.github.io/evolver-tools/try.sh | bash
# ═══════════════════════════════════════════════════════════════
set -e

# ─── Colors ───
BOLD='\033[1m'
DIM='\033[2m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
NC='\033[0m'

# ─── Header ───
clear 2>/dev/null || true
echo ""
echo -e "  ${CYAN}${BOLD}╔══════════════════════════════════════════════════╗${NC}"
echo -e "  ${CYAN}${BOLD}║    ⚡ EVOLVER Tools — 60-Second Interactive Demo  ║${NC}"
echo -e "  ${CYAN}${BOLD}║    261 CLI tools · zero deps · one pip install   ║${NC}"
echo -e "  ${CYAN}${BOLD}╚══════════════════════════════════════════════════╝${NC}"
echo ""

# ─── Auto-install if needed ───
if ! command -v evtool &>/dev/null; then
    echo -e "  ${YELLOW}📦 Installing evolver-tools (just once)...${NC}"
    pip install -q evolver-tools 2>&1 | tail -1 || {
        echo -e "  ${RED}✗ Install failed. Try: pip install evolver-tools${NC}"
        exit 1
    }
    echo -e "  ${GREEN}✅ Installed!${NC}\n"
fi

# ─── Demo Tools ───

demo() {
    local num=$1
    local title=$2
    local cmd=$3
    echo ""
    echo -e "  ${CYAN}${BOLD}─── Demo ${num} ───────────────────────────────────────────${NC}"
    echo -e "  ${DIM}${title}${NC}"
    echo ""
    eval "$cmd" 2>/dev/null || echo -e "  ${RED}(offline — needs network)${NC}"
    echo ""
    sleep 1
}

# ─── 1. ASCII Banner ───
demo 1 "ascii-banner — Large ASCII art in 5 fonts" \
    "evtool ascii-banner 'HELLO WORLD'"

# ─── 2. Cowsay ───
demo 2 "cowsay — ASCII animals (cow, tux, dragon, bunny)" \
    "evtool cowsay 'Install me: pip install evolver-tools'"

# ─── 3. Chart ───
demo 3 "chart-cli — Bar / line / pie / histogram in terminal" \
    "echo 'Mon,Tue,Wed,Thu,Fri,Sat,Sun
120,85,200,45,160,95,210' | evtool chart-cli bar"

# ─── 4. QR Code ───
demo 4 "qrcode — Generate QR codes in terminal" \
    "evtool qrcode 'https://github.com/evolver-dev/evolver-tools'"

# ─── 5. Emoji Search ───
demo 5 "emoji-cli — Search 1,800+ emoji from terminal" \
    "evtool emoji-cli rocket && sleep 0.3 && evtool emoji-cli fire && sleep 0.3 && evtool emoji-cli star"

# ─── 6. Crypto Ticker ───
demo 6 "crypto-price — Live crypto prices (CoinGecko)" \
    "evtool crypto-price bitcoin ethereum solana 2>/dev/null | head -6 || echo '  (needs internet connection)'"

# ─── 7. Dice Roll ───
demo 7 "dice-roll — d4, d6, d8, d10, d12, d20, d100" \
    "evtool dice-roll --dice 3d6"

# ─── 8. Cron Pretty ───
demo 8 "cron-pretty — Describe cron in plain English" \
    "evtool cron-pretty '*/5 9-17 * * 1-5'"

# ─── 9. Random Password ───
demo 9 "passgen — Strong passwords / passphrases" \
    "evtool passgen --length 20 --numbers --symbols 2>/dev/null | head -3 || echo '  password generator ready!'"

# ─── 10. JSON Pretty Print ───
demo 10 "json-pretty — Format / validate / minify JSON" \
    "echo '{\"name\":\"evolver\",\"tools\":261,\"deps\":0,\"features\":[\"csv\",\"json\",\"crypto\",\"net\"]}' | evtool json-pretty"

# ─── Footer ───
clear 2>/dev/null || true
echo ""
echo -e "  ${GREEN}${BOLD}╔══════════════════════════════════════════════════╗${NC}"
<<<<<<< HEAD
echo -e "  ${GREEN}${BOLD}║          🎉 Demo Complete! 261 tools ready      ║${NC}"
=======
echo -e "  ${GREEN}${BOLD}║          🎉 Demo Complete!                      ║${NC}"
echo -e "  ${GREEN}${BOLD}║     evtool list  —  Browse all 261 tools       ║${NC}"
>>>>>>> main
echo -e "  ${GREEN}${BOLD}╚══════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${CYAN}${BOLD}What's next:${NC}"
echo ""
echo -e "  ${BOLD}Try any tool:${NC}"
echo -e "    evtool list              # Browse all 261 tools"
echo -e "    evtool <name> --help     # Tool-specific help"
echo -e "    evtool showcase          # 12 featured tools"
echo ""
echo -e "  ${BOLD}Explore categories:${NC}"
echo -e "    evtool categories        # 18 categories"
echo ""
echo -e "  ${BOLD}Show some love:${NC}"
echo -e "    ${DIM}GitHub:${NC}  https://github.com/evolver-dev/evolver-tools"
echo -e "    ${DIM}PyPI:${NC}    pip install evolver-tools"
echo -e "    ${DIM}Docs:${NC}    https://evolver-dev.github.io/evolver-tools"
echo ""
echo -e "  ${YELLOW}⭐ Star the repo if you like what you see!${NC}"
echo ""
