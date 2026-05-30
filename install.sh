#!/usr/bin/env bash
set -e

# ═══════════════════════════════════════════════════════════════
#  EVOLVER CLI Tools — Installer
#  One-liner: curl -sSL https://evolver.dev/install.sh | bash
# ═══════════════════════════════════════════════════════════════

BOLD='\033[1m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# ─── Configuration ────────────────────────────────────────────────────────────
VERSION="1.4.0"
WHEEL_URL="https://evolver.dev/download/evolver_tools-${VERSION}-py3-none-any.whl"
# Fallback: install from PyPI (once published)
PYPI_PACKAGE="evolver-tools"

# ─── Pre-flight checks ────────────────────────────────────────────────────────

echo -e "${CYAN}${BOLD}"
echo "  ╔═══════════════════════════════════════════════╗"
echo "  ║        EVOLVER CLI Tools Installer v${VERSION}       ║"
echo "  ╚═══════════════════════════════════════════════╝"
echo -e "${NC}"

# Check Python
if command -v python3 &>/dev/null; then
    PYTHON="python3"
elif command -v python &>/dev/null; then
    PYTHON="python"
else
    echo -e "${RED}✗ Python not found. Install Python 3.8+ first.${NC}"
    exit 1
fi

PY_VER=$($PYTHON -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "  ✓ Python ${PY_VER} found at $(command -v $PYTHON)"

# Check pip
if ! $PYTHON -m pip --version &>/dev/null; then
    echo -e "${RED}✗ pip not found. Install pip first.${NC}"
    echo "  Try: $PYTHON -m ensurepip --upgrade"
    exit 1
fi
echo -e "  ✓ pip found"

# ─── Install ──────────────────────────────────────────────────────────────────

echo ""
echo -e "${YELLOW}Installing evolver-tools v${VERSION}...${NC}"

# Strategy 1: Direct wheel download (preferred)
if [ -n "$WHEEL_URL" ] && command -v curl &>/dev/null; then
    echo -e "  → Downloading wheel from ${WHEEL_URL}"
    TMP_DIR=$(mktemp -d)
    trap "rm -rf $TMP_DIR" EXIT

    if curl -fsSL "$WHEEL_URL" -o "$TMP_DIR/evolver_tools.whl" 2>/dev/null; then
        echo -e "  → Installing wheel..."
        if $PYTHON -m pip install "$TMP_DIR/evolver_tools.whl" --no-cache-dir 2>&1; then
            echo -e "${GREEN}✓ Installed from wheel!${NC}"
        else
            echo -e "${YELLOW}  ⚠ Wheel install failed, falling back to PyPI...${NC}"
            $PYTHON -m pip install "$PYPI_PACKAGE" 2>&1 && \
                echo -e "${GREEN}✓ Installed from PyPI!${NC}" || \
                { echo -e "${RED}✗ Install failed${NC}"; exit 1; }
        fi
    else
        echo -e "${YELLOW}  ⚠ Wheel download failed, trying PyPI...${NC}"
        $PYTHON -m pip install "$PYPI_PACKAGE" 2>&1 && \
            echo -e "${GREEN}✓ Installed from PyPI!${NC}" || \
            { echo -e "${RED}✗ Install failed${NC}"; exit 1; }
    fi

# Strategy 2: PyPI (fallback)
else
    echo -e "  → Installing from PyPI..."
    $PYTHON -m pip install "$PYPI_PACKAGE" 2>&1 && \
        echo -e "${GREEN}✓ Installed from PyPI!${NC}" || \
        { echo -e "${RED}✗ Install failed. Try: pip install $PYPI_PACKAGE${NC}"; exit 1; }
fi

# ─── Verify ───────────────────────────────────────────────────────────────────

echo ""
echo -e "${CYAN}─ Verifying installation...${NC}"

if command -v evtool &>/dev/null; then
    echo -e "  ✓ evtool CLI available"
    TOOL_COUNT=$(evtool list 2>&1 | grep -c "^  [a-z]" || true)
    echo -e "  ✓ ${TOOL_COUNT:-31}+ tools installed"
elif $PYTHON -c "import evolver_tools" 2>/dev/null; then
    echo -e "  ✓ evolver_tools Python package imported"
else
    echo -e "${YELLOW}  ⚠ Verification skipped — try 'evtool list' manually${NC}"
fi

# ─── Done ─────────────────────────────────────────────────────────────────────

echo ""
echo -e "${GREEN}${BOLD}  ┌──────────────────────────────────────────────┐${NC}"
echo -e "${GREEN}${BOLD}  │       EVOLVER CLI Tools installed! 🎉        │${NC}"
echo -e "${GREEN}${BOLD}  └──────────────────────────────────────────────┘${NC}"
echo ""
echo -e "  ${CYAN}Quick start:${NC}"
echo -e "    evtool list           # List all 31 tools"
echo -e "    evtool ff < file      # Fuzzy search lines"
echo -e "    evtool sqlite-cli db  # Query SQLite databases"
echo -e "    evtool sysmon         # System monitor"
echo ""
echo -e "  ${CYAN}Or use individual CLIs:${NC}"
echo -e "    ff < file             # Fuzzy finder"
echo -e "    hashsum file.iso      # Checksum calculator"
echo -e "    siege-lite -c 10 url  # HTTP load testing"
echo ""
echo -e "  ${CYAN}Docs:${NC} https://evolver.dev"
echo -e "  ${CYAN}Code:${NC} https://github.com/evolver/evolver-tools"
echo ""
echo -e "  ${YELLOW}Tip: Run 'evtool list' to see all available tools${NC}"
echo ""
