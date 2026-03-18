# SPEAR Earth System Data Assistant

### Steps to running this chatbot locally:
#### *Please Note: You will either need an API key or Ollama with a local model downloaded in order to use the chatbot features.

1. Clone this repository into your terminal.

2. Copy the 'chatbot.conf.template' and rename as 'chatbot.conf'. Edit the paths in the conf as needed.

3. In /chatbot, copy and rename '.env.example' to '.env' in the same directory. Add your API keys or paths to local Ollama models.

## To enable authentication:

4. In /chatbot, edit .env and set:
```bash
AUTH_ENABLED=false
```

## To run the application:

4. From the main directory:
```bash
./start.sh
```

5. Access the chatbot from browser at: https://localhost:8501

If you do not see the dashboard at the link above, ensure the application has proper permissions to to bind to the local port (8501).
