# SPEAR Earth System Data Assistant

Copy the chatbot.conf.template and rename as chatbot.conf. Edit the paths in the conf as needed.

In /chatbot, copy and rename .env.example to .env in the same directory. Add your API keys or paths to local Ollama models.

To run the application from the main directory:
```bash
./start.sh
```

Access the chatbot from browser at: https://localhost:8501

If you do not see the dashboard at the link above, ensure the application has proper permissions to to bind to the local port (8501).
