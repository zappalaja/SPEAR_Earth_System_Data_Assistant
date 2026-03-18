#!/usr/bin/env bash
#
# Climate Chatbot Launcher with CMIP6 Zarr MCP Server
#
# This script starts the complete chatbot stack:
#   1. RAG Service (document retrieval) - Port 8002
#   2. MCP Server with Zarr tools - Port 8000
#   3. Streamlit Chatbot UI - Port 8501
#
# Usage: ./start.sh
#
# Press Ctrl+C to stop all services
#

set -e  # Exit on error

# ============================================================
# Configuration
# ============================================================

# Resolve project directory from the script's own location — no hardcoded paths
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

RAG_DIR="$PROJECT_DIR/rag-service"
MCP_DIR="$PROJECT_DIR/mcp-server"
CHATBOT_DIR="$PROJECT_DIR/chatbot"

RAG_PORT=8002
MCP_PORT=8000
CHATBOT_PORT=8501

# PID and log files
PID_DIR="/tmp/climate_chatbot_zarr_pids"
LOG_DIR="${LOG_DIR:-$PID_DIR}"
mkdir -p "$PID_DIR" "$LOG_DIR"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# ============================================================
# Load external config (CHROMA paths, conda env, etc.)
# ============================================================
CONFIG_FILE="$PROJECT_DIR/chatbot.conf"
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}ERROR: Missing config file: $CONFIG_FILE${NC}"
    echo "Copy chatbot.conf.template to chatbot.conf and fill in your paths."
    exit 1
fi
source "$CONFIG_FILE"

# ============================================================
# Cleanup function - stops all services gracefully
# ============================================================
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down all services...${NC}"

    # Kill RAG service
    if [ -f "$PID_DIR/rag.pid" ]; then
        RAG_PID=$(cat "$PID_DIR/rag.pid")
        if kill -0 "$RAG_PID" 2>/dev/null; then
            echo "  Stopping RAG service (PID $RAG_PID)..."
            kill "$RAG_PID" 2>/dev/null || true
        fi
        rm -f "$PID_DIR/rag.pid"
    fi

    # Kill MCP server
    if [ -f "$PID_DIR/mcp.pid" ]; then
        MCP_PID=$(cat "$PID_DIR/mcp.pid")
        if kill -0 "$MCP_PID" 2>/dev/null; then
            echo "  Stopping MCP server (PID $MCP_PID)..."
            kill "$MCP_PID" 2>/dev/null || true
        fi
        rm -f "$PID_DIR/mcp.pid"
    fi

    # Kill chatbot
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

# Trap Ctrl+C and other exit signals
trap cleanup SIGINT SIGTERM EXIT

# ============================================================
# Helper: Wait for a service to be ready
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
echo "  Climate Chatbot Launcher"
echo "  with CMIP6 Zarr MCP Server"
echo "============================================================"
echo ""

# Check for uv (needed for MCP server)
if ! command -v uv >/dev/null 2>&1; then
    echo -e "${RED}ERROR: 'uv' is not installed or not on PATH${NC}"
    echo "Install it from: https://github.com/astral-sh/uv"
    exit 1
fi

# Check for conda (needed for RAG service)
if [ ! -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    echo -e "${RED}ERROR: Miniconda not found at ~/miniconda3${NC}"
    exit 1
fi

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
    conda activate "${CONDA_ENV:-rag}"

    export CHROMA_PERSIST_DIR
    export CHROMA_COLLECTION
    export EMBED_MODEL

    cd "$RAG_DIR"
    exec uvicorn rag_service:app --host 0.0.0.0 --port $RAG_PORT >> "$LOG_DIR/rag.log" 2>&1
) &
echo $! > "$PID_DIR/rag.pid"

wait_for_service "RAG Service" "http://localhost:$RAG_PORT/health" || {
    # Try alternate endpoint if /health doesn't exist
    wait_for_service "RAG Service" "http://localhost:$RAG_PORT/" || exit 1
}

# ============================================================
# Service 2: Start MCP Server (with Zarr tools)
# ============================================================
echo -e "${BLUE}[2/3] Starting MCP Server (CMIP6 Zarr)...${NC}"

(
    cd "$MCP_DIR"
    exec uv run python -m spear_mcp --transport sse --host 0.0.0.0 --port $MCP_PORT >> "$LOG_DIR/mcp.log" 2>&1
) &
echo $! > "$PID_DIR/mcp.pid"

wait_for_service "MCP Server" "http://localhost:$MCP_PORT/health" || {
    # Give it a moment if health check doesn't exist
    sleep 3
    echo -e "  ${YELLOW}(assuming ready)${NC}"
}

# ============================================================
# Service 3: Start Chatbot
# ============================================================
echo -e "${BLUE}[3/3] Starting Chatbot...${NC}"

cd "$CHATBOT_DIR"

# Create/activate virtual environment
if [ ! -d "venv" ]; then
    echo "  Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Install dependencies
echo "  Installing dependencies..."
pip install -q -r requirements.txt

# Check .env file exists
if [ ! -f .env ]; then
    echo -e "  ${YELLOW}WARNING: No .env file found!${NC}"
    if [ -f .env.template ]; then
        cp .env.template .env
        echo -e "  ${GREEN}Created .env from template${NC}"
    else
        echo -e "  ${RED}No .env.template found either. You may need to create .env manually.${NC}"
    fi
fi

# ============================================================
# All services started - show status
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
echo "    • SPEAR NetCDF tools (original)"
echo "    • CMIP6 Zarr tools (new)"
echo "      - test_cmip6_connection()"
echo "      - get_zarr_store_info()"
echo "      - query_zarr_data()"
echo "      - get_zarr_summary_statistics()"
echo ""
echo "  Logs:"
echo "    RAG: tail -f $LOG_DIR/rag.log"
echo "    MCP: tail -f $LOG_DIR/mcp.log"
echo ""
echo -e "${YELLOW}  Press Ctrl+C to stop all services${NC}"
echo "============================================================"
echo ""

# Run chatbot in foreground (trap will handle cleanup on Ctrl+C)
streamlit run SPEAR_Earth_System_Data_Assistant.py --server.port $CHATBOT_PORT
