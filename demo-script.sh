#!/usr/bin/env bash
# ============================================================================
# evolver-tools DEMO SCRIPT — for asciinema recording
#
# Records a ~30-second demo showing evolver-tools in action.
#   pip install evolver-tools  →  261 CLI tools, zero deps.
#
# Usage:
#   pip install agg
#   asciinema rec -c "bash demo-script.sh" demo.cast
#   agg --speed 1.5 --font-size 14 demo.cast demo.gif
#
# Then post the GIF on X/Twitter, Reddit, HN, or your blog.
# ============================================================================

export TERM="${TERM:-xterm-256color}"

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

_cmd() {
  echo -e "${GREEN}$ ${YELLOW}$1${NC}"
  sleep 0.5
  eval "$1" 2>&1 | head -15
  sleep 0.3
}

echo -e "${BOLD}${CYAN}━━━ evolver-tools ─ 261 CLI tools, zero deps ━━━${NC}"
echo
echo "One pip install replaces 30+ packages:"
echo "  jq, csvkit, figlet, htop, httpie, nmap..."
echo "All pure Python stdlib. No npm. No cargo."
sleep 2

echo
echo -e "${BOLD}1/5  Install ─────────────────────────${NC}"
_cmd "pip install evolver-tools"

echo
echo -e "${BOLD}2/5  CSV Stats (replaces csvkit) ─────${NC}"
_cmd "printf 'name,role,score\\nAlice,dev,92\\nBob,ops,78\\nCarol,dev,88\\nDave,ml,95\\n' > /tmp/demo.csv && evtool csv-stats /tmp/demo.csv"

echo
echo -e "${BOLD}3/5  JSON (replaces jq) ──────────────${NC}"
_cmd "printf '{\"users\":[{\"name\":\"Alice\",\"role\":\"dev\"},{\"name\":\"Bob\",\"role\":\"ops\"}]}' > /tmp/demo.json && evtool json-pretty /tmp/demo.json"

echo
echo -e "${BOLD}4/5  System Info (replaces neofetch) ─${NC}"
_cmd "evtool system-info --brief"

echo
echo -e "${BOLD}5/5  ASCII Art (replaces figlet) ─────${NC}"
_cmd "evtool figlet 'evolver tools | 261'"

echo
echo -e "${BOLD}${CYAN}━━━ Done ───────────────────────────${NC}"
echo
echo -e "pip install evolver-tools"
echo "https://evolver-dev.github.io/evolver-tools/"
echo
