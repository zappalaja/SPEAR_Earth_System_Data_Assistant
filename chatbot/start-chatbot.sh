#!/bin/bash
# Start SPEAR Climate Chatbot Container
# This script stops any existing container and starts a fresh one with the .env file

set -e  # Exit on error

CONTAINER_NAME="spear-chatbot"
IMAGE_NAME="localhost/spear-chatbot"
PORT="8501"

echo "🚀 Starting SPEAR Climate Chatbot..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create one from env.template:"
    echo "  cp env.template .env"
    echo "  # Then edit .env with your API key"
    exit 1
fi

# Stop and remove existing container if it exists
if podman ps -a --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    echo "🛑 Stopping existing container: ${CONTAINER_NAME}..."
    podman stop ${CONTAINER_NAME} 2>/dev/null || true
    echo "🗑️  Removing existing container: ${CONTAINER_NAME}..."
    podman rm ${CONTAINER_NAME} 2>/dev/null || true
fi

# Check for any other containers using port 8501
OTHER_CONTAINERS=$(podman ps --format "{{.Names}} {{.Ports}}" | grep ":${PORT}->" | awk '{print $1}' || true)
if [ ! -z "$OTHER_CONTAINERS" ]; then
    echo "⚠️  Found containers using port ${PORT}:"
    echo "🛑 Stopping them..."
    for container in $OTHER_CONTAINERS; do
        echo "  - Stopping $container"
        podman stop $container 2>/dev/null || true
        podman rm $container 2>/dev/null || true
    done
fi

# Start the container
echo "▶️  Starting container..."
podman run -d \
    --name ${CONTAINER_NAME} \
    --env-file .env \
    -p ${PORT}:${PORT} \
    ${IMAGE_NAME}

echo "✅ Container started successfully!"
echo "📡 Access the chatbot at: http://localhost:${PORT}"
echo ""
echo "To view logs: podman logs -f ${CONTAINER_NAME}"
echo "To stop: podman stop ${CONTAINER_NAME}"
