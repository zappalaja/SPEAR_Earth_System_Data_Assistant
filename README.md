# SPEAR Earth System Data Assistant

An AI chatbot for exploring GFDL SPEAR climate model data, powered by MCP tools and RAG-based document retrieval.

## Quick Start

> **Note:** You will need either a **Gemini API key**, **Anthropic API key**, or **Ollama with a local model** to use the chatbot features.

### 1. Clone the repository

```bash
git clone https://github.com/zappalaja/SPEAR_Earth_System_Data_Assistant.git
cd SPEAR_Earth_System_Data_Assistant
```

### 2. Run the setup script

This installs Miniconda (if needed) and creates two conda environments:
- **spear** — runs the chatbot, MCP server, and RAG service (Python 3.13)
- **nougat** — runs Nougat OCR for PDF ingestion (Python 3.11)

```bash
./setup_and_test.sh
```

### 3. Add your API keys

In `/chatbot`, copy and rename `.env.example` to `.env` and add your API key(s):

```bash
GEMINI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

### 4. Run the application

```bash
conda activate spear
./start_unified.sh
```

Access the chatbot in your browser at: **http://localhost:8501**

If you do not see the dashboard, ensure the application has proper permissions to bind to the local port (8501).

## Configuration

`chatbot.conf` — Copy `chatbot.conf.template` to `chatbot.conf` and edit paths if needed. The setup script does this automatically.

`chatbot/.env` — Additional options:

| Setting | Description |
|---|---|
| `AUTH_ENABLED=true` | Enable login authentication (see `users.yaml`) |
| `PERSIST_CONVERSATIONS=true` | Restore conversation history between sessions |
| `DEFAULT_PROVIDER=gemini` | Set default LLM provider (`gemini` or `claude`) |
| `RAG_ENABLED=true` | Enable RAG document retrieval |

## Architecture

The application runs three services:

| Service | Port | Description |
|---|---|---|
| Streamlit Chatbot | 8501 | User-facing web interface |
| MCP Server | 8000 | Climate data tools (SPEAR NetCDF + CMIP6 Zarr) |
| RAG Service | 8002 | Document retrieval backed by ChromaDB |

## PDF Ingestion

The chatbot supports uploading new climate research PDFs for ingestion. This requires the **nougat** conda environment (created by `setup_and_test.sh`). Ingestion runs automatically through the chatbot UI — the Nougat OCR stage activates its own environment in a subprocess.

## Container Deployment

Instructions coming soon!

## Legacy Setup

The original `start.sh` launcher is still available for users with the previous multi-environment setup (separate `rag` conda env, chatbot venv, and `uv` for the MCP server).
