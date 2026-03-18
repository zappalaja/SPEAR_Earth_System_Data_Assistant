#!/usr/bin/env bash
#
# Entrypoint for the all-in-one SPEAR Climate Chatbot container.
# Starts RAG, MCP, and Streamlit services, then waits for shutdown.
#

set -e

LOG_DIR="/app/logs"
mkdir -p "$LOG_DIR"

# ---------- Check for API keys ----------
if [ -z "$GEMINI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
    echo ""
    echo "============================================================"
    echo "  ERROR: No API key provided."
    echo "============================================================"
    echo ""
    echo "  At least one LLM API key is required to run the chatbot."
    echo ""
    echo "  Pass keys with -e flags:"
    echo "    podman run -e GEMINI_API_KEY=your_key -p 8501:8501 spear-earth-system-data-assistant"
    echo ""
    echo "  Or create an env file and pass it:"
    echo "    podman run --env-file your.env -p 8501:8501 spear-earth-system-data-assistant"
    echo ""
    echo "  Supported keys: GEMINI_API_KEY, ANTHROPIC_API_KEY"
    echo "============================================================"
    exit 1
fi

echo ""
echo "============================================================"
echo "  SPEAR Earth System Data Assistant"
echo "============================================================"
echo ""

# Show which providers are configured
[ -n "$GEMINI_API_KEY" ]    && echo "  Gemini API:    configured"
[ -n "$ANTHROPIC_API_KEY" ] && echo "  Anthropic API: configured"
echo ""

# Cleanup on exit
cleanup() {
    echo "Shutting down services..."
    kill "$RAG_PID" "$MCP_PID" 2>/dev/null || true
    wait "$RAG_PID" "$MCP_PID" 2>/dev/null || true
    echo "All services stopped."
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# ---------- Service 1: RAG ----------
if [ "${RAG_ENABLED:-true}" = "true" ]; then
    echo "[1/3] Starting RAG Service on port 8002..."
    cd /app/rag-service
    uvicorn rag_service:app --host 0.0.0.0 --port 8002 >> "$LOG_DIR/rag.log" 2>&1 &
    RAG_PID=$!

    # Wait for RAG to be ready
    for i in $(seq 1 30); do
        if curl -sf http://localhost:8002/health >/dev/null 2>&1 || \
           curl -sf http://localhost:8002/ >/dev/null 2>&1; then
            echo "  RAG Service ready."
            break
        fi
        sleep 1
    done
else
    echo "[1/3] RAG Service disabled."
    RAG_PID=""
fi

# ---------- Service 2: MCP Server ----------
echo "[2/3] Starting MCP Server on port 8000..."
cd /app/mcp-server
uv run python -m spear_mcp --transport sse --host 0.0.0.0 --port 8000 >> "$LOG_DIR/mcp.log" 2>&1 &
MCP_PID=$!

# Wait for MCP to be ready
for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
        echo "  MCP Server ready."
        break
    fi
    sleep 1
done

# ---------- Service 3: Chatbot (foreground) ----------
echo "[3/3] Starting Chatbot on port 8501..."
echo ""
echo "  Chatbot available at: http://localhost:8501"
echo ""
cd /app/chatbot
exec streamlit run SPEAR_Earth_System_Data_Assistant.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.serverAddress=localhost
