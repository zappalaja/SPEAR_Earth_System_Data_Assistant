#!/bin/bash
# SPEAR Climate Chatbot - View Logs Script (Podman)

echo "Viewing SPEAR Climate Chatbot logs..."
echo "Press Ctrl+C to exit"
echo ""

podman logs -f spear-chatbot
