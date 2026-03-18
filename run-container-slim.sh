#!/usr/bin/env bash
#
# Run the SPEAR Earth System Data Assistant container (slim image, no ingestion).
#
# Usage: ./run-container-slim.sh
#
# If chatbot/.env exists, API keys are read from there.
# Otherwise, the script prompts for a key.
# Document ingestion (/ingest) is not available in this variant.
#

set -e

# ---- Option: paste your API key here so you don't need a .env file or prompt ----
GEMINI_API_KEY=""
ANTHROPIC_API_KEY=""
# ---------------------------------------------------------------------------------

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="docker.io/zappalaja/spear_earth_system_data_assistant:1.0-slim"
CONTAINER_NAME="spear-assistant"

# Paths to mount
CHROMA_DB="$PROJECT_DIR/rag-service/ingestion/chroma_db"
MERGED_MD="$PROJECT_DIR/rag-service/ingestion/nougat_merged_md"
ENV_FILE="$PROJECT_DIR/chatbot/.env"

# Pull image if not available locally
if ! podman image exists "$IMAGE"; then
    echo "Pulling $IMAGE..."
    podman pull "$IMAGE"
fi

# Stop existing container if running
if podman ps -a --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    echo "Stopping existing container..."
    podman stop "$CONTAINER_NAME" 2>/dev/null || true
    podman rm "$CONTAINER_NAME" 2>/dev/null || true
fi

# Build the run command
RUN_ARGS=(
    --name "$CONTAINER_NAME"
    -v "$CHROMA_DB:/app/chroma_db:Z"
    -v "$MERGED_MD:/app/nougat_merged_md:Z"
    -e "AUTH_ENABLED=true"
    -e "STREAMLIT_THEME_BASE=dark"
    -e "DEFAULT_MODEL=gemini-3-flash-preview"
    -p 8501:8501
)

# Priority: hardcoded in script → .env file → interactive prompt
if [ -n "$GEMINI_API_KEY" ] || [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "Using API keys from script variables"
    [ -n "$GEMINI_API_KEY" ]    && RUN_ARGS+=(-e "GEMINI_API_KEY=$GEMINI_API_KEY")
    [ -n "$ANTHROPIC_API_KEY" ] && RUN_ARGS+=(-e "ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY")
elif [ -f "$ENV_FILE" ]; then
    echo "Using API keys from $ENV_FILE"
    RUN_ARGS+=(--env-file "$ENV_FILE")
else
    echo ""
    echo "No .env file found. Enter an API key to start the chatbot."
    echo ""
    echo "  1) Gemini API key"
    echo "  2) Anthropic API key"
    echo ""
    read -rp "Choice [1/2]: " choice

    case "$choice" in
        1)
            read -rp "Gemini API key: " api_key
            RUN_ARGS+=(-e "GEMINI_API_KEY=$api_key" -e "DEFAULT_PROVIDER=gemini")
            ;;
        2)
            read -rp "Anthropic API key: " api_key
            RUN_ARGS+=(-e "ANTHROPIC_API_KEY=$api_key" -e "DEFAULT_PROVIDER=claude")
            ;;
        *)
            echo "Invalid choice."
            exit 1
            ;;
    esac
fi

echo "Starting $IMAGE..."
podman run "${RUN_ARGS[@]}" "$IMAGE"
