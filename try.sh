#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
#  EVOLVER Tools — Power Demo
#  One-liner: curl -sL https://evolver-dev.github.io/evolver-tools/try.sh | bash
#  Shows 5 tools in 5 seconds — real demos, real output.
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
echo -e "  ${CYAN}${BOLD}║    ⚡ EVOLVER Tools — Power Demo                ║${NC}"
echo -e "  ${CYAN}${BOLD}║    260 CLI tools · zero deps · one pip install ║${NC}"
echo -e "  ${CYAN}${BOLD}╚══════════════════════════════════════════════════╝${NC}"
echo ""

# ─── Install ───
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

# ─── Demo 1: System Info (practical) ───
echo ""
echo -e "  ${CYAN}${BOLD}─── ⚙️  System at a Glance ──────────────────────────${NC}"
echo -e "  ${DIM}Replace 'neofetch' + 'htop' + 'df' with one command:${NC}"
echo ""
echo -e "  ${GREEN}$ evtool sys-info${NC}"
evtool sys-info 2>/dev/null || true

# ─── Demo 2: JSON Processing (developer need) ───
echo ""
echo -e "  ${CYAN}${BOLD}─── { } JSON Processing — No jq Required ─────────${NC}"
echo -e "  ${DIM}Pretty-print, validate, and query JSON without jq:${NC}"
echo ""
JSON_DATA='{"tools":260,"deps":0,"lang":"python","categories":["data","network","system","security","devops","text","fun","conversion"]}'
echo -e "  ${GREEN}$ echo '$JSON_DATA' | evtool json-pretty${NC}"
echo "$JSON_DATA" | evtool json-pretty 2>/dev/null || echo "$JSON_DATA"

# ─── Demo 3: Password Generator (practical utility) ───
echo ""
echo -e "  ${CYAN}${BOLD}─── 🔐 Password Generator ──────────────────────────${NC}"
echo -e "  ${DIM}Generate secure passwords in one command:${NC}"
echo ""
echo -e "  ${GREEN}$ evtool gen-password 24 --symbols --numbers${NC}"
evtool gen-password 24 --symbols --numbers 2>/dev/null || true

# ─── Demo 4: CSV Data Analysis (killer feature) ───
echo ""
echo -e "  ${CYAN}${BOLD}─── 📊 CSV Data Analysis — No Pandas Required ──────${NC}"
echo -e "  ${DIM}Generate a CSV and run full stats in one line:${NC}"
echo ""
cat > /tmp/_demo_sales.csv << 'CSVEOF'
product,price,quantity,category,region
Widget A,12.99,150,gadgets,NA
Widget B,24.99,85,gadgets,EU
Gadget X,49.99,42,tools,NA
Gadget Y,39.99,67,tools,APAC
Widget C,8.99,200,gadgets,APAC
Widget D,19.99,120,gadgets,EU
Tool Kit,89.99,15,tools,NA
Widget E,14.99,95,gadgets,NA
Gadget Z,59.99,30,tools,EU
Widget F,6.99,300,gadgets,APAC
CSVEOF
echo -e "  ${GREEN}$ evtool csv-stats /tmp/_demo_sales.csv${NC}"
evtool csv-stats /tmp/_demo_sales.csv 2>/dev/null || true
rm -f /tmp/_demo_sales.csv

# ─── Demo 5: Network — Quick DNS Check ───
echo ""
echo -e "  ${CYAN}${BOLD}─── 🌐 DNS Lookup — Replace 'nslookup/dig' ─────────${NC}"
echo -e "  ${DIM}Check DNS records quickly without dig/nslookup:${NC}"
echo ""
echo -e "  ${GREEN}$ evtool dns-lookup github.com --type A${NC}"
evtool dns-lookup github.com --type A 2>/dev/null || true

# ─── Fun: ASCII Banner ───
echo ""
echo -e "  ${CYAN}${BOLD}─── 🎨 ASCII Art — For Good Measure ───────────────${NC}"
echo ""
echo -e "  ${GREEN}$ evtool ascii-banner 'pip install evolver'${NC}"
evtool ascii-banner "pip install evolver" 2>/dev/null | head -6

# ─── Footer ───
echo ""
echo -e "  ${GREEN}${BOLD}╔══════════════════════════════════════════════════╗${NC}"
echo -e "  ${GREEN}${BOLD}║          🎉 Demo Complete!                      ║${NC}"
echo -e "  ${GREEN}${BOLD}║     ${NC}${CYAN}260 CLI tools · 0 deps · 1 pip install${NC}     ${GREEN}║${NC}"
echo -e "  ${GREEN}${BOLD}║                                                  ║${NC}"
echo -e "  ${GREEN}${BOLD}║  ${NC}Browse all:  ${CYAN}evtool list${NC}                    ${GREEN}║${NC}"
echo -e "  ${GREEN}${BOLD}║  ${NC}Search:      ${CYAN}evtool search <query>${NC}           ${GREEN}║${NC}"
echo -e "  ${GREEN}${BOLD}║  ${NC}Help:        ${CYAN}evtool help <name>${NC}              ${GREEN}║${NC}"
echo -e "  ${GREEN}${BOLD}╚══════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${YELLOW}⭐ Star on GitHub:${NC} https://github.com/evolver-dev/evolver-tools"
echo -e "  ${YELLOW}📖 Full docs:${NC}     https://evolver-dev.github.io/evolver-tools"
echo -e "  ${YELLOW}🐍 PyPI:${NC}           https://pypi.org/project/evolver-tools/"
echo ""