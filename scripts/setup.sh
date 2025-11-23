#!/bin/bash

# LifeMetrics Setup Script
# This script helps set up LifeMetrics for first-time users

set -e

echo "======================================"
echo "LifeMetrics Setup Script"
echo "======================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed."
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Error: Docker Compose is not installed."
    echo "Please install Docker Compose first: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✓ Docker is installed"
echo "✓ Docker Compose is installed"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env

    # Generate secret keys
    if command -v python3 &> /dev/null; then
        echo "Generating secret keys..."

        SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
        JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

        # Update .env file
        sed -i.bak "s/your-secret-key-change-this-in-production/$SECRET_KEY/g" .env
        sed -i.bak "s/your-jwt-secret-key/$JWT_SECRET_KEY/g" .env

        echo "✓ Secret keys generated"
    else
        echo "Warning: Python3 not found. Please manually set SECRET_KEY and JWT_SECRET_KEY in .env"
    fi

    echo ""
    echo "⚠️  IMPORTANT: Please edit .env and set the following:"
    echo "   - POSTGRES_PASSWORD"
    echo "   - REDIS_PASSWORD"
    echo "   - MINIO_ROOT_PASSWORD"
    echo "   - ENCRYPTION_KEY"
    echo ""
    read -p "Press Enter to continue after editing .env..."
else
    echo "✓ .env file already exists"
fi

echo ""
echo "Starting Docker containers..."
docker-compose up -d

echo ""
echo "Waiting for services to be ready..."
sleep 10

echo ""
echo "Checking service health..."

# Check if services are running
if docker ps | grep -q lifemetrics-postgres; then
    echo "✓ PostgreSQL is running"
else
    echo "✗ PostgreSQL is not running"
fi

if docker ps | grep -q lifemetrics-redis; then
    echo "✓ Redis is running"
else
    echo "✗ Redis is not running"
fi

if docker ps | grep -q lifemetrics-ollama; then
    echo "✓ Ollama is running"
else
    echo "✗ Ollama is not running"
fi

if docker ps | grep -q lifemetrics-backend; then
    echo "✓ Backend is running"
else
    echo "✗ Backend is not running"
fi

if docker ps | grep -q lifemetrics-frontend; then
    echo "✓ Frontend is running"
else
    echo "✗ Frontend is not running"
fi

echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Download Ollama models:"
echo "   docker exec -it lifemetrics-ollama ollama pull llama3.2"
echo ""
echo "2. Access the application:"
echo "   - Frontend: http://localhost:3000"
echo "   - Backend API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/api/docs"
echo "   - MinIO Console: http://localhost:9001"
echo ""
echo "For more information, see docs/SETUP.md"
echo ""
