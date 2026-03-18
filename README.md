# SPEAR Earth System Data Assistant

### Steps to running this chatbot locally:
#### *Please Note: You will either need an API key or Ollama with a local model downloaded in order to use the chatbot features.

1. Clone this repository into your terminal.

2. Copy the 'chatbot.conf.template' and rename as 'chatbot.conf'. Edit the paths in the conf as needed.

3. In /chatbot, copy and rename '.env.example' to '.env' in the same directory. Add your API key(s).

## To enable authentication:

4. In /chatbot, edit .env and set:
```bash
AUTH_ENABLED=true
```

## To enable persistent conversation history between sessions:

5. In /chatbot, edit .env and set:
```bash
PERSIST_CONVERSATIONS=true
```

## To run the application:

6. From the main directory:
```bash
./start.sh
```

7. Access the chatbot from browser at: https://localhost:8501

If you do not see the dashboard at the link above, ensure the application has proper permissions to to bind to the local port (8501).
