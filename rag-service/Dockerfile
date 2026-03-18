FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY rag_service.py .
COPY start_rag_api.sh .
RUN chmod +x start_rag_api.sh

# Environment variables (can be overridden at runtime)
ENV CHROMA_PERSIST_DIR=/app/chroma_db
ENV CHROMA_COLLECTION=nougat_merged
ENV EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Expose port
EXPOSE 8002

# Run the service
CMD ["./start_rag_api.sh"]
