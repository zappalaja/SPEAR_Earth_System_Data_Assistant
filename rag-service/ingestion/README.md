# SPEAR-RAG-Ingestion
Tools needed to take pdf files, convert them to markdown, and the embed them in ChromaDB on Linux. Designed for SPEAR.

# Nougat → RAG Pipeline

This repository implements a **two-stage document processing and retrieval pipeline** for academic PDFs:

1. **Nougat OCR + merge + cleaning**
2. **RAG ingestion (chunking + embeddings + Chroma persistence)**

The stages are intentionally separated and run in **different Conda environments** to keep dependencies clean and reproducible.

Jupyter notebooks are optional and **not required** to run the pipeline.

---

## Pipeline overview

```text
PDFs
  ↓
[Stage 1] Nougat OCR + merge + clean   (conda env: nougat)
  ↓
Clean Markdown
  ↓
[Stage 2] RAG ingestion (chunk + embed + persist)   (conda env: rag_new)
  ↓
Chroma vector database


## Setup

### Nougat environment
```bash
conda env create -f envs/nougat.conda.yml
conda activate nougat
pip install -r envs/nougat.pip.txt
```

### RAG environment
```bash
conda env create -f envs/rag.conda.yml
conda activate rag_new
pip install -r envs/rag.pip.txt
```
### Stage 1: Nougat OCR → merged, cleaned Markdown
Configure paths

Edit:
```bash
scripts/nougat_stage.conf
```

Key variables:
```text
INPUT_PDF_DIR=...     # directory containing input PDFs
NOUGAT_OUT_DIR=...    # raw Nougat outputs
MERGED_MD_DIR=...     # final cleaned Markdown output
LOG_DIR=...           # per-PDF Nougat logs
CONDA_ENV=nougat
```
Run Stage 1
```bash
bash scripts/nougat_stage.sh scripts/nougat_stage.conf
```

This stage:

- Activates the nougat Conda environment

- Runs Nougat on every *.pdf in INPUT_PDF_DIR

- Captures per-PDF logs in LOG_DIR

- Merges Nougat output into one Markdown file per PDF

- Removes boilerplate text once, upstream

- Writes provenance files:

  pdf_sha256.json

  manifest.json

Output structure:
```text
MERGED_MD_DIR/
├── paper1.md
├── paper2.md
├── pdf_sha256.json
└── manifest.json
```
### Stage 2: RAG ingestion (Markdown → Chroma)
Configure paths

Edit:
```bash
scripts/rag_stage.conf
```

Key variables:
```text
MERGED_MD_DIR=...     # output from Stage 1
CHROMA_DIR=...        # Chroma persistence directory
COLLECTION=...        # Chroma collection name
EMBEDDING_MODEL=...   # must match query usage
CHUNK_SIZE=1200
CHUNK_OVERLAP=150
CONDA_ENV=rag_new
```
Run Stage 2
```bash
bash scripts/rag_stage.sh scripts/rag_stage.conf
```

This stage:

- Activates the rag Conda environment

- Loads cleaned Markdown files

- Chunks documents

- Embeds text using the configured model

- Persists embeddings into Chroma

This stage is write-only:


### Querying the vector database

To query the database from the terminal:
```bash
conda activate rag

./scripts/query_chroma.py \
  --chroma_dir /path/to/chroma_db \
  --collection nougat_merged \
  --query "Atlantic Meridional Overturning circulation"
```

This is a read-only operation and does not modify the database.

### Design notes

- Each stage explicitly activates its required Conda environment

- Boilerplate removal happens only in Stage 1

- Stage 2 assumes inputs are already clean

- Stages can be run independently

- Scripts are suitable for batch jobs, cron, SLURM, or CI pipelines

- Environment separation avoids dependency conflicts between OCR and RAG tooling

### Common pitfalls

- Do not run both stages in the same Conda environment

- Do not re-embed with a different embedding model unless rebuilding the database

- If PDFs change, rerun Stage 1 before Stage 2

- If only chunking parameters change, rerun Stage 2 only



