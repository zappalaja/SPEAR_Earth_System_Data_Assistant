#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 path/to/rag_stage.conf"
  exit 1
fi

CONF="$1"
if [[ ! -f "$CONF" ]]; then
  echo "Config not found: $CONF"
  exit 1
fi

# shellcheck disable=SC1090
source "$CONF"

mkdir -p "$CHROMA_DIR"

if [[ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]]; then
  source "$HOME/miniconda3/etc/profile.d/conda.sh"
elif [[ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]]; then
  source "$HOME/anaconda3/etc/profile.d/conda.sh"
else
  echo "Could not find conda.sh. Please ensure conda is installed."
  exit 1
fi

conda activate "$CONDA_ENV"

echo "Using conda env: $CONDA_ENV"
echo "Merged md:    $MERGED_MD_DIR"
echo "Chroma dir:   $CHROMA_DIR"
echo "Collection:   $COLLECTION"
echo "Embeddings:   $EMBEDDING_MODEL"
echo "Chunking:     size=$CHUNK_SIZE overlap=$CHUNK_OVERLAP"
echo

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$SCRIPT_DIR/rag_ingest.py"

if [[ ! -f "$PY" ]]; then
  echo "rag_ingest.py not found next to this script. Expected: $PY"
  exit 1
fi

python "$PY"   --md_dir "$MERGED_MD_DIR"   --chroma_dir "$CHROMA_DIR"   --collection "$COLLECTION"   --embedding_model "$EMBEDDING_MODEL"   --chunk_size "$CHUNK_SIZE"   --chunk_overlap "$CHUNK_OVERLAP"

echo "Done."
