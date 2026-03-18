#!/usr/bin/env bash
set -e

# --------------------------------------------------
# RAG configuration
# For local dev, paths resolve relative to this script.
# For containers, override with env vars or use /app defaults.
# --------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INGESTION_DIR="${SCRIPT_DIR}/ingestion"

export CHROMA_PERSIST_DIR="${CHROMA_PERSIST_DIR:-${INGESTION_DIR}/chroma_db}"
export CHROMA_COLLECTION="${CHROMA_COLLECTION:-nougat_merged}"
export EMBED_MODEL="${EMBED_MODEL:-sentence-transformers/all-MiniLM-L6-v2}"
export MERGED_MD_DIR="${MERGED_MD_DIR:-${INGESTION_DIR}/nougat_merged_md}"
export INGESTION_SCRIPTS_DIR="${INGESTION_SCRIPTS_DIR:-${INGESTION_DIR}/scripts}"
export INPUT_PDF_DIR="${INPUT_PDF_DIR:-${INGESTION_DIR}/pdfs}"

# --------------------------------------------------
# Start FastAPI
# --------------------------------------------------
exec uvicorn rag_service:app --host 0.0.0.0 --port 8002

