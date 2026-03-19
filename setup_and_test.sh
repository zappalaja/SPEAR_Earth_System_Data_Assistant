#!/usr/bin/env bash
#
# SPEAR Earth System Data Assistant — Full Environment Setup & Verification
#
# This script bootstraps everything from scratch on a clean Linux machine:
#   1. Installs Miniconda if missing
#   2. Creates the "spear" conda env (Python 3.13) — runs chatbot, MCP server, RAG service
#   3. Creates the "nougat" conda env (Python 3.11) — runs Nougat OCR for PDF ingestion
#   4. Creates config files from templates if missing
#   5. Runs a comprehensive verification of all imports across both environments
#
# Usage:
#   ./setup_and_test.sh           # Full setup + verify (both envs)
#   ./setup_and_test.sh --verify  # Verify only (skip setup, just test imports)
#

set -uo pipefail

# ============================================================
# Configuration
# ============================================================
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERIFY_ONLY=false

for arg in "$@"; do
    case "$arg" in
        --verify)  VERIFY_ONLY=true ;;
        --help|-h)
            echo "Usage: $0 [--verify]"
            echo ""
            echo "  (no flags)  Full setup + verification (creates both conda envs)"
            echo "  --verify    Skip setup, only run verification tests"
            echo ""
            echo "Two conda environments are created:"
            echo "  spear   — Python 3.13, runs chatbot + MCP server + RAG service"
            echo "  nougat  — Python 3.11, runs Nougat OCR for PDF ingestion"
            echo ""
            echo "Only Miniconda is required. This script will auto-install it if missing."
            exit 0
            ;;
    esac
done

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

pass()  { PASS=$((PASS + 1)); echo -e "  ${GREEN}✓${NC} $1"; }
fail()  { FAIL=$((FAIL + 1)); echo -e "  ${RED}✗${NC} $1"; }
warn()  { WARN=$((WARN + 1)); echo -e "  ${YELLOW}⚠${NC} $1"; }
header(){ echo ""; echo -e "${BLUE}${BOLD}── $1 ──${NC}"; }

# ============================================================
# PHASE 1: System Prerequisites
# ============================================================
header "System Prerequisites"

# --- curl ---
if command -v curl &>/dev/null; then
    pass "curl found"
else
    fail "curl not found — install with: sudo apt install curl"
fi

# --- git ---
if command -v git &>/dev/null; then
    pass "git found"
else
    warn "git not found — install with: sudo apt install git"
fi

# --- Miniconda (auto-install if missing) ---
if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    pass "Miniconda found at ~/miniconda3"
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
elif [ "$VERIFY_ONLY" = false ]; then
    echo -e "  ${YELLOW}Miniconda not found — installing to ~/miniconda3...${NC}"
    MINICONDA_INSTALLER="/tmp/Miniconda3-latest-Linux-x86_64.sh"
    if curl -fsSL -o "$MINICONDA_INSTALLER" "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"; then
        bash "$MINICONDA_INSTALLER" -b -p "$HOME/miniconda3"
        rm -f "$MINICONDA_INSTALLER"
        source "$HOME/miniconda3/etc/profile.d/conda.sh"
        pass "Miniconda installed at ~/miniconda3"
    else
        fail "Failed to download Miniconda installer"
    fi
else
    fail "Miniconda not found at ~/miniconda3 — run setup (without --verify) to auto-install"
fi

# ============================================================
# PHASE 2: Setup (skip if --verify)
# ============================================================
if [ "$VERIFY_ONLY" = false ]; then

    # ----------------------------------------------------------
    # 2a. Config files
    # ----------------------------------------------------------
    header "Configuration Files"

    if [ ! -f "$PROJECT_DIR/chatbot.conf" ]; then
        cp "$PROJECT_DIR/chatbot.conf.template" "$PROJECT_DIR/chatbot.conf"
        sed -i "s|CHROMA_PERSIST_DIR=.*|CHROMA_PERSIST_DIR=\"$PROJECT_DIR/rag-service/ingestion/chroma_db\"|" "$PROJECT_DIR/chatbot.conf"
        pass "Created chatbot.conf (CHROMA_PERSIST_DIR set to project path)"
    else
        pass "chatbot.conf already exists"
    fi

    if [ ! -f "$PROJECT_DIR/chatbot/.env" ]; then
        if [ -f "$PROJECT_DIR/chatbot/.env.example" ]; then
            cp "$PROJECT_DIR/chatbot/.env.example" "$PROJECT_DIR/chatbot/.env"
            warn "Created chatbot/.env from example — YOU MUST add your API keys!"
            echo -e "    Edit: $PROJECT_DIR/chatbot/.env"
            echo -e "    Set GEMINI_API_KEY and/or ANTHROPIC_API_KEY"
        fi
    else
        pass "chatbot/.env already exists"
    fi

    # ----------------------------------------------------------
    # 2b. Conda "spear" environment (chatbot + MCP server + RAG service)
    # ----------------------------------------------------------
    header "Conda Environment: spear (main application)"

    if conda info --envs 2>/dev/null | grep -qw "spear"; then
        pass "Conda env 'spear' already exists"
    else
        echo "  Creating conda env 'spear' from environment.yml..."
        echo "  (This may take 10-20 minutes depending on your connection)"
        if conda env create -f "$PROJECT_DIR/environment.yml" 2>&1 | tail -5; then
            pass "Conda env 'spear' created"
        else
            fail "Failed to create conda env 'spear'"
        fi
    fi

    # ----------------------------------------------------------
    # 2c. Conda "nougat" environment (PDF ingestion via Nougat OCR)
    # ----------------------------------------------------------
    header "Conda Environment: nougat (PDF ingestion)"

    if conda info --envs 2>/dev/null | grep -qw "nougat"; then
        pass "Conda env 'nougat' already exists"
    else
        echo "  Creating conda env 'nougat' with Python 3.11 + nougat-ocr..."
        echo "  (This is large — includes PyTorch + CUDA. May take 15-30 minutes)"
        if conda create -n nougat python=3.11 -y 2>&1 | tail -3; then
            echo "  Installing nougat pip dependencies..."
            if "$HOME/miniconda3/envs/nougat/bin/pip" install \
                nougat-ocr==0.1.17 \
                torch torchvision \
                pytorch-lightning \
                chromadb \
                timm==0.5.4 \
                albumentations==1.3.0 \
                transformers==4.30.2 \
                tokenizers==0.13.3 \
                pypdfium2==4.24.0 \
                pypdf \
                2>&1 | tail -5; then
                pass "Conda env 'nougat' created with all dependencies"
            else
                fail "Conda env 'nougat' created but pip install failed"
            fi
        else
            fail "Failed to create conda env 'nougat'"
        fi
    fi
fi

# ============================================================
# PHASE 3: Verification
# ============================================================

# ----------------------------------------------------------
header "Verifying: spear environment (chatbot + MCP server + RAG service)"

SPEAR_PY="$HOME/miniconda3/envs/spear/bin/python"
if [ -f "$SPEAR_PY" ]; then
    pass "spear env found (Python $($SPEAR_PY --version 2>&1 | awk '{print $2}'))"

    # All imports across chatbot, MCP server, and RAG service
    SPEAR_IMPORTS=(
        # Shared
        "numpy" "xarray" "aiohttp" "matplotlib" "h5netcdf" "netCDF4"
        "PIL" "s3fs" "fsspec" "pydantic"
        # Chatbot
        "streamlit" "dotenv" "boto3" "PyPDF2" "httpx" "mcp"
        "anthropic" "google.generativeai" "streamlit_authenticator"
        "yaml" "bcrypt"
        # MCP Server
        "aiofiles" "async_lru" "bs4" "cartopy" "cftime" "fastmcp"
        "loguru" "pydap" "dask" "zarr"
        # RAG Service
        "fastapi" "uvicorn" "langchain_chroma" "langchain_huggingface"
        "sentence_transformers" "chromadb"
        # Ingestion support
        "pypdf"
    )

    for mod in "${SPEAR_IMPORTS[@]}"; do
        if "$SPEAR_PY" -c "import $mod" 2>/dev/null; then
            pass "$mod"
        else
            fail "$mod — not importable in spear env"
        fi
    done

    # Test MCP server can be imported with PYTHONPATH
    if PYTHONPATH="$PROJECT_DIR/mcp-server/src" "$SPEAR_PY" -c "from spear_mcp.server import main" 2>/dev/null; then
        pass "MCP server (spear_mcp) importable via PYTHONPATH"
    else
        fail "MCP server (spear_mcp) not importable — check mcp-server/src/"
    fi

    # Test RAG service can be imported
    if (cd "$PROJECT_DIR/rag-service" && "$SPEAR_PY" -c "from rag_service import app" 2>/dev/null); then
        pass "RAG service (rag_service) importable"
    else
        fail "RAG service (rag_service) not importable"
    fi

    echo ""
    echo "  Key versions:"
    "$SPEAR_PY" -c "
import streamlit, xarray, numpy, fastmcp, chromadb, sentence_transformers
print(f'    streamlit:             {streamlit.__version__}')
print(f'    xarray:                {xarray.__version__}')
print(f'    numpy:                 {numpy.__version__}')
print(f'    fastmcp:               {fastmcp.__version__}')
print(f'    chromadb:              {chromadb.__version__}')
print(f'    sentence-transformers: {sentence_transformers.__version__}')
try:
    import anthropic; print(f'    anthropic:             {anthropic.__version__}')
except: pass
" 2>/dev/null || warn "Could not print spear versions"
else
    fail "spear conda env not found — run setup first"
fi

# ----------------------------------------------------------
header "Verifying: nougat environment (PDF ingestion)"

NOUGAT_PY="$HOME/miniconda3/envs/nougat/bin/python"
if [ -f "$NOUGAT_PY" ]; then
    pass "nougat env found (Python $($NOUGAT_PY --version 2>&1 | awk '{print $2}'))"

    NOUGAT_IMPORTS=(
        "nougat" "torch" "transformers" "chromadb"
        "pytorch_lightning" "timm" "albumentations" "PIL" "pypdf"
    )

    for mod in "${NOUGAT_IMPORTS[@]}"; do
        if "$NOUGAT_PY" -c "import $mod" 2>/dev/null; then
            pass "$mod"
        else
            fail "$mod — not importable in nougat env"
        fi
    done

    # Check nougat CLI is available
    if "$HOME/miniconda3/envs/nougat/bin/nougat" --help &>/dev/null; then
        pass "nougat CLI available"
    else
        fail "nougat CLI not working"
    fi

    # GPU check
    GPU_AVAIL=$("$NOUGAT_PY" -c "import torch; print(torch.cuda.is_available())" 2>/dev/null || echo "unknown")
    if [ "$GPU_AVAIL" = "True" ]; then
        pass "CUDA GPU available for nougat OCR"
    else
        warn "No CUDA GPU detected — nougat ingestion will run on CPU (slow)"
    fi
else
    fail "nougat conda env not found — run setup first"
fi

# ----------------------------------------------------------
header "Verifying: Configuration Files"

if [ -f "$PROJECT_DIR/chatbot.conf" ]; then
    pass "chatbot.conf exists"
    source "$PROJECT_DIR/chatbot.conf"
    if [ -d "${CHROMA_PERSIST_DIR:-}" ]; then
        pass "CHROMA_PERSIST_DIR points to existing directory"
    else
        warn "CHROMA_PERSIST_DIR=${CHROMA_PERSIST_DIR:-<unset>} — directory does not exist yet"
    fi
else
    fail "chatbot.conf missing — copy chatbot.conf.template"
fi

if [ -f "$PROJECT_DIR/chatbot/.env" ]; then
    pass "chatbot/.env exists"
    if grep -q "your_gemini_api_key_here\|your_anthropic_api_key_here" "$PROJECT_DIR/chatbot/.env" 2>/dev/null; then
        warn "chatbot/.env still has placeholder API keys — update before running!"
    else
        pass "API keys appear to be set (not placeholder values)"
    fi
else
    fail "chatbot/.env missing — copy from .env.example and add API keys"
fi

if [ -f "$PROJECT_DIR/rag-service/ingestion/chroma_db/chroma.sqlite3" ]; then
    pass "Pre-populated ChromaDB found (ingested papers included)"
else
    warn "No pre-populated ChromaDB — RAG queries may return no results"
fi

# ============================================================
# Summary
# ============================================================
echo ""
echo "============================================================"
echo -e "${BOLD}  Verification Summary${NC}"
echo "============================================================"
echo -e "  ${GREEN}Passed:  $PASS${NC}"
echo -e "  ${RED}Failed:  $FAIL${NC}"
echo -e "  ${YELLOW}Warnings: $WARN${NC}"
echo ""

if [ "$FAIL" -eq 0 ]; then
    echo -e "  ${GREEN}${BOLD}All checks passed!${NC} The application is ready to run."
    echo ""
    echo "  To start:  conda activate spear && ./start_unified.sh"
    echo "  Then open: http://localhost:8501"
else
    echo -e "  ${RED}${BOLD}$FAIL check(s) failed.${NC} Fix the issues above, then re-run this script."
fi

if [ "$WARN" -gt 0 ]; then
    echo -e "  ${YELLOW}$WARN warning(s)${NC} — review above for details."
fi

echo ""
exit $FAIL
