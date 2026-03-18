# SPEAR Climate Chatbot

An AI-powered chatbot for exploring SPEAR (Seamless system for Prediction and EArth system Research) climate model data.

This chatbot is designed to be run alongside the SPEAR MCP server for AWS hosted output:

https://github.com/zappalaja/spear-mcp-test

## Features

- **Direct SPEAR Data Access**: Query climate data from AWS S3 (historical and SSP5-8.5 scenarios)
- **Visualization**: Generate plots
- **Ollama AI Integration**: Powered by local Ollama models (default: Gemma 3)
- **Smart Size Management**: Automatic query validation and size checking
- **Geographic Conversion**: Auto-converts longitude formats (-180/180 ↔ 0-360)
- **Expert Knowledge Base**: Built-in climate science terminology and SPEAR model info
- **Confidence Assessment**: Qualitative self-assessment of response accuracy

## Reccomended Setup Using Podman Pod


Containers to be publicly available in the future! Currently only for private use.


## Quick Start Outside of Containers

Python Virtual Environment

1. **Clone and setup**
   ```bash
   git clone https://github.com/zappalaja/spear-climate-chatbot.git
   cd spear-climate-chatbot
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Ollama**
   ```bash
   cp .env.template .env
   # Edit .env if Ollama is not running locally:
   # OLLAMA_BASE_URL=http://localhost:11434
   ```
   Ensure Ollama is running and the model is available:
   ```bash
   ollama pull gemma3
   ```

4. **Run the application**
   
   Make executable and run **`run-local.sh`**:
   ```bash
   chmod +x run-local.sh
   ./run_local.sh
   ```
   Or:
   ```bash
   streamlit run chatbot_app.py
   ```

6. **Access the chatbot**
   Open your browser to: http://localhost:8501

## Configuration

### Environment Variables

Create a `.env` file with:

```bash
OLLAMA_BASE_URL=http://localhost:11434
```

If you run Ollama on another host, update the URL accordingly (omit any trailing `/api`, `/api/chat`, or `/v1/chat/completions`). If you want to use the OpenAI-compatible endpoint, set `OLLAMA_BASE_URL` to `http://localhost:11434/v1`.

### Customization

The chatbot's behavior can be customized by editing:

- **`controlled_vocabulary.py`**: Language policies, prohibited topics, terminology
- **`variable_definitions.py`**: Climate variable definitions and units
- **`spear_model_info.py`**: SPEAR model specifications and scenarios
- **`confidence_assessment.py`**: Qualitative confidence assessment criteria
- **`ai_config.py`**: Model settings, conversation tone, welcome message

## Podman Deployment

### Build the image

```bash
podman build -t spear-chatbot .
```

## Usage Examples


### Browse Available Data

```
"What variables are available in SPEAR?"
"List the ensemble members for historical scenario"
"Show me metadata for temperature data"
```

### Get Explanations

```
"What is SSP5-8.5?"
"Explain the difference between tas and tasmax"
"What are ensemble members?"
```


### Size Management

The chatbot automatically prevents queries that would exceed API token limits:

- **Maximum**: 200,000 tokens per request
- **Safe threshold**: 100,000 tokens (for data)
- **Automatic blocking**: Queries exceeding limits show alternatives
- **Suggestions**: Smaller regions, shorter time periods, or Python code

## System Requirements

### Minimum

- Python 3.11+
- 2GB RAM
- Internet connection (for S3 access)
- Ollama running locally (or reachable over the network)

## Troubleshooting

### "ModuleNotFoundError"

Make sure you've installed all dependencies:
```bash
pip install -r requirements.txt
```

### "Ollama connection failed"

Check your `.env` file has the correct URL:
```bash
OLLAMA_BASE_URL=http://localhost:11434
```

### "Query too large" errors

The chatbot will show alternatives. Try:
- Smaller geographic region
- Shorter time period
- Request spatial averages

### Docker connection issues

Ensure port 8501 is available:
```bash
lsof -i :8501
```
