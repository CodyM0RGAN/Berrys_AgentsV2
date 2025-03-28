#!/bin/bash

# Setup script for Project-based Multi-Agent System Framework

# Exit on error
set -e

# Print commands
set -x

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please update the .env file with your actual values."
fi

# Create logs directory
mkdir -p logs

# Create Docker volumes
echo "Creating Docker volumes..."
docker volume create postgres_data
docker volume create redis_data
docker volume create ollama_models

# Build Docker images
echo "Building Docker images..."
docker-compose build

# Install pre-commit hooks
if command -v pre-commit &> /dev/null; then
    echo "Installing pre-commit hooks..."
    pre-commit install
fi

# Create Python virtual environment
if command -v python3 &> /dev/null; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    
    # Install Python dependencies
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
    
    # Install development dependencies
    pip install black isort mypy pytest pytest-cov
    
    # Deactivate virtual environment
    deactivate
fi

# Install Node.js dependencies for web dashboard
if command -v npm &> /dev/null; then
    echo "Installing Node.js dependencies for web dashboard..."
    cd services/web-dashboard
    npm install
    cd ../..
fi

echo "Setup completed successfully!"
echo "You can now start the services with: docker-compose up -d"
