#!/usr/bin/env bash
#
# Climate Chatbot Launcher (Unified Conda Environment)
#
# This script starts the complete chatbot stack using the single "spear" conda env:
#   1. RAG Service (document retrieval) - Port 8002
#   2. MCP Server - Port 8000
#   3. Streamlit Chatbot UI - Port 8501
#
# Prerequisites:
#   conda env create -f environment.yml
#   cp chatbot.conf.template chatbot.conf
#   cp chatbot/.env.example chatbot/.env  # add your API keys
#
# Usage: ./start_unified.sh
#
# Press Ctrl+C to stop all services
#

set -e

# ============================================================
# Configuration
# ============================================================
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

RAG_DIR="$PROJECT_DIR/rag-service"
MCP_DIR="$PROJECT_DIR/mcp-server"
CHATBOT_DIR="$PROJECT_DIR/chatbot"

RAG_PORT=8002
MCP_PORT=8000
CHATBOT_PORT=8501

CONDA_ENV_NAME="spear"

# PID and log files
PID_DIR="/tmp/climate_chatbot_zarr_pids"
LOG_DIR="${LOG_DIR:-$PID_DIR}"
mkdir -p "$PID_DIR" "$LOG_DIR"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# ============================================================
# Load external config (CHROMA paths, etc.)
# ============================================================
CONFIG_FILE="$PROJECT_DIR/chatbot.conf"
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}ERROR: Missing config file: $CONFIG_FILE${NC}"
    echo "Copy chatbot.conf.template to chatbot.conf and fill in your paths."
    exit 1
fi
source "$CONFIG_FILE"

# ============================================================
# Cleanup function
# ============================================================
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down all services...${NC}"

    if [ -f "$PID_DIR/rag.pid" ]; then
        RAG_PID=$(cat "$PID_DIR/rag.pid")
        if kill -0 "$RAG_PID" 2>/dev/null; then
            echo "  Stopping RAG service (PID $RAG_PID)..."
            kill "$RAG_PID" 2>/dev/null || true
        fi
        rm -f "$PID_DIR/rag.pid"
    fi

    if [ -f "$PID_DIR/mcp.pid" ]; then
        MCP_PID=$(cat "$PID_DIR/mcp.pid")
        if kill -0 "$MCP_PID" 2>/dev/null; then
            echo "  Stopping MCP server (PID $MCP_PID)..."
            kill "$MCP_PID" 2>/dev/null || true
        fi
        rm -f "$PID_DIR/mcp.pid"
    fi

    if [ -f "$PID_DIR/chatbot.pid" ]; then
        CHATBOT_PID=$(cat "$PID_DIR/chatbot.pid")
        if kill -0 "$CHATBOT_PID" 2>/dev/null; then
            echo "  Stopping Chatbot (PID $CHATBOT_PID)..."
            kill "$CHATBOT_PID" 2>/dev/null || true
        fi
        rm -f "$PID_DIR/chatbot.pid"
    fi

    echo -e "${GREEN}All services stopped.${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# ============================================================
# Wait helper
# ============================================================
wait_for_service() {
    local name="$1"
    local url="$2"
    local max_attempts=30
    local attempt=1

    echo -n "  Waiting for $name to be ready"
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            echo -e " ${GREEN}✓${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done

    echo -e " ${RED}✗ TIMEOUT${NC}"
    echo -e "${RED}ERROR: $name failed to start within ${max_attempts}s${NC}"
    return 1
}

# ============================================================
# Check prerequisites
# ============================================================
echo ""
echo "============================================================"
echo "  Climate Chatbot Launcher (Unified Environment)"
echo "============================================================"
echo ""

# Initialize conda
if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
else
    echo -e "${RED}ERROR: Miniconda not found at ~/miniconda3${NC}"
    exit 1
fi

# Check the spear env exists
if ! conda info --envs 2>/dev/null | grep -qw "$CONDA_ENV_NAME"; then
    echo -e "${RED}ERROR: Conda environment '$CONDA_ENV_NAME' not found.${NC}"
    echo "Create it with: conda env create -f environment.yml"
    exit 1
fi

# Activate the unified environment for the entire script
conda activate "$CONDA_ENV_NAME"
echo -e "${GREEN}✓${NC} Conda environment '$CONDA_ENV_NAME' activated (Python $(python --version 2>&1 | awk '{print $2}'))"

# Verify directories exist
for dir in "$RAG_DIR" "$MCP_DIR" "$CHATBOT_DIR"; do
    if [ ! -d "$dir" ]; then
        echo -e "${RED}ERROR: Directory not found: $dir${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✓${NC} All prerequisites met"
echo "  Logs: $LOG_DIR/{rag,mcp}.log"
echo ""

# ============================================================
# Service 1: Start RAG Service
# ============================================================
echo -e "${BLUE}[1/3] Starting RAG Service...${NC}"

(
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
    conda activate "$CONDA_ENV_NAME"

    export CHROMA_PERSIST_DIR
    export CHROMA_COLLECTION
    export EMBED_MODEL
    export CONDA_ENV="$CONDA_ENV_NAME"
    export INGESTION_SCRIPTS_DIR="$RAG_DIR/ingestion/scripts"
    export MERGED_MD_DIR="$RAG_DIR/ingestion/nougat_merged_md"
    export INPUT_PDF_DIR="$RAG_DIR/ingestion/pdfs"

    cd "$RAG_DIR"
    exec uvicorn rag_service:app --host 0.0.0.0 --port $RAG_PORT >> "$LOG_DIR/rag.log" 2>&1
) &
echo $! > "$PID_DIR/rag.pid"

wait_for_service "RAG Service" "http://localhost:$RAG_PORT/health" || {
    wait_for_service "RAG Service" "http://localhost:$RAG_PORT/" || exit 1
}

# ============================================================
# Service 2: Start MCP Server
# ============================================================
echo -e "${BLUE}[2/3] Starting MCP Server...${NC}"

(
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
    conda activate "$CONDA_ENV_NAME"

    cd "$MCP_DIR"
    # Add src/ to PYTHONPATH so python can find the spear_mcp package
    export PYTHONPATH="$MCP_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
    exec python -m spear_mcp --transport sse --host 0.0.0.0 --port $MCP_PORT >> "$LOG_DIR/mcp.log" 2>&1
) &
echo $! > "$PID_DIR/mcp.pid"

wait_for_service "MCP Server" "http://localhost:$MCP_PORT/health" || {
    sleep 3
    echo -e "  ${YELLOW}(assuming ready)${NC}"
}

# ============================================================
# Service 3: Start Chatbot
# ============================================================
echo -e "${BLUE}[3/3] Starting Chatbot...${NC}"

cd "$CHATBOT_DIR"

# Check .env file exists
if [ ! -f .env ]; then
    echo -e "  ${YELLOW}WARNING: No .env file found!${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "  ${GREEN}Created .env from template — add your API keys!${NC}"
    else
        echo -e "  ${RED}No .env.example found. Create .env manually.${NC}"
    fi
fi

# ============================================================
# All services started
# ============================================================
echo ""
echo "============================================================"
echo -e "  ${GREEN}✓ All services started!${NC}"
echo "============================================================"
echo ""
echo "  RAG Service:  http://localhost:$RAG_PORT"
echo "  MCP Server:   http://localhost:$MCP_PORT"
echo "                (NetCDF + Zarr tools available)"
echo "  Chatbot:      http://localhost:$CHATBOT_PORT"
echo ""
echo -e "${YELLOW}  Available MCP Tools:${NC}"
echo "    • SPEAR NetCDF tools "
echo "    • CMIP6 Zarr tools "
echo ""
echo "  Logs:"
echo "    RAG: tail -f $LOG_DIR/rag.log"
echo "    MCP: tail -f $LOG_DIR/mcp.log"
echo ""
echo -e "${YELLOW}  Press Ctrl+C to stop all services${NC}"
echo "============================================================"
echo ""

# Run chatbot in foreground — no venv needed, spear env is active
streamlit run SPEAR_Earth_System_Data_Assistant.py --server.port $CHATBOT_PORT
