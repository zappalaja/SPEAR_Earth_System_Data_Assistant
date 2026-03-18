# Containerfile for SPEAR Climate Chatbot (All-in-One)
#
# Runs all three services in a single container:
#   - RAG Service (port 8002) — query/retrieval + ingestion via conda envs
#   - MCP Server (port 8000)
#   - Streamlit Chatbot (port 8501)
#
# API keys are NEVER baked into the image. Pass them at runtime:
#   podman run --env-file .env -p 8501:8501 spear-chatbot
#
# ChromaDB and merged markdown must be volume-mounted:
#   -v /path/to/chroma_db:/app/chroma_db
#   -v /path/to/nougat_merged_md:/app/nougat_merged_md
#
# For GPU-accelerated Nougat ingestion, add:
#   --device nvidia.com/gpu=all (or --gpus all for Docker)

FROM python:3.13-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    bash \
    && rm -rf /var/lib/apt/lists/*

# ---------- Install Miniconda (for ingestion pipeline conda envs) ----------
RUN curl -fsSL https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
        -o /tmp/miniconda.sh && \
    bash /tmp/miniconda.sh -b -p /opt/conda && \
    rm /tmp/miniconda.sh
ENV PATH="/opt/conda/bin:$PATH"

# Accept Anaconda TOS for default channels (required since Miniconda 25.x)
RUN conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main && \
    conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r

# ---------- Create conda environments for ingestion ----------
COPY rag-service/ingestion/envs/nougat.yml /tmp/nougat.yml
COPY rag-service/ingestion/envs/rag.yml /tmp/rag.yml

# nougat.yml creates env named "nougat" — matches code as-is
RUN conda env create -f /tmp/nougat.yml && conda clean -afy
# rag.yml creates env named "rag_new" — rename to "rag" to match chatbot.conf and rag_service.py
RUN conda env create -f /tmp/rag.yml -n rag && conda clean -afy
RUN rm /tmp/nougat.yml /tmp/rag.yml

# Install uv (needed for MCP server)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# ---------- RAG Service dependencies ----------
COPY rag-service/requirements.txt /app/rag-service/requirements.txt
RUN pip install --no-cache-dir -r /app/rag-service/requirements.txt

# ---------- Chatbot dependencies ----------
COPY chatbot/requirements.txt /app/chatbot/requirements.txt
RUN pip install --no-cache-dir -r /app/chatbot/requirements.txt

# ---------- MCP Server dependencies (installed via uv) ----------
COPY mcp-server/ /app/mcp-server/

RUN cd /app/mcp-server && uv sync --frozen

# ---------- Copy application code ----------
COPY rag-service/rag_service.py /app/rag-service/
COPY rag-service/ingestion/scripts/ /app/rag-service/ingestion/scripts/
COPY chatbot/*.py chatbot/*.yaml /app/chatbot/
COPY chatbot/pages/ /app/chatbot/pages/
COPY chatbot/avatars/ /app/chatbot/avatars/
COPY chatbot/bot_avatar/ /app/chatbot/bot_avatar/
COPY chatbot/background/ /app/chatbot/background/

# ---------- Copy entrypoint ----------
COPY container-entrypoint.sh /app/container-entrypoint.sh
RUN chmod +x /app/container-entrypoint.sh

# Create log and data directories
RUN mkdir -p /app/logs /app/chatbot/chat_logs /app/chroma_db /app/nougat_merged_md /app/pdfs

# ---------- Default environment ----------
# Service URLs (internal to container — localhost since all services run here)
ENV MCP_SERVER_URL=http://localhost:8000
ENV RAG_API_URL=http://localhost:8002
ENV RAG_ENABLED=true
ENV RAG_TOP_K=2
ENV LOGGING_ENABLED=true
ENV CHAT_LOG_DIR=/app/chatbot/chat_logs

# ChromaDB and document store defaults (override via env or volume mount)
ENV CHROMA_PERSIST_DIR=/app/chroma_db
ENV CHROMA_COLLECTION=nougat_merged
ENV EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2
ENV MERGED_MD_DIR=/app/nougat_merged_md

# Ingestion pipeline paths
ENV INGESTION_SCRIPTS_DIR=/app/rag-service/ingestion/scripts
ENV INPUT_PDF_DIR=/app/pdfs

# Symlink so ingestion scripts find conda.sh at $HOME/miniconda3/
# (scripts look for ~/miniconda3/etc/profile.d/conda.sh)
RUN ln -s /opt/conda /root/miniconda3

# API keys must be provided at runtime via:
#   --env-file .env
#   -e GEMINI_API_KEY=your_key
#   -e ANTHROPIC_API_KEY=your_key

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["/app/container-entrypoint.sh"]
