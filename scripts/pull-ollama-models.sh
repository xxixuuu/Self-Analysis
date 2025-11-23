#!/bin/bash

# Pull Ollama models script

set -e

echo "======================================"
echo "Ollama Models Download"
echo "======================================"
echo ""

# Check if Ollama container is running
if ! docker ps | grep -q lifemetrics-ollama; then
    echo "Error: Ollama container is not running."
    echo "Please start the containers first: docker-compose up -d"
    exit 1
fi

echo "Pulling Ollama models..."
echo ""

# Pull llama3.2 (recommended, ~4.7GB)
echo "1. Pulling llama3.2 (recommended, ~4.7GB)..."
docker exec -it lifemetrics-ollama ollama pull llama3.2
echo "✓ llama3.2 downloaded"
echo ""

# Ask if user wants to pull additional models
read -p "Pull mistral model? (7B, lighter alternative) (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "2. Pulling mistral..."
    docker exec -it lifemetrics-ollama ollama pull mistral
    echo "✓ mistral downloaded"
    echo ""
fi

read -p "Pull gemma2 model? (9B, good for summarization) (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "3. Pulling gemma2..."
    docker exec -it lifemetrics-ollama ollama pull gemma2
    echo "✓ gemma2 downloaded"
    echo ""
fi

echo "======================================"
echo "Models Download Complete!"
echo "======================================"
echo ""
echo "Available models:"
docker exec lifemetrics-ollama ollama list
echo ""
echo "You can now use LifeMetrics with local AI analysis!"
echo ""
