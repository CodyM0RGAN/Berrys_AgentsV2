#!/bin/bash

# Run tests for Model Orchestration service
# This script runs the tests and generates a coverage report

# Set environment variables for testing
export PYTHONPATH=$PYTHONPATH:$(pwd)
export ENVIRONMENT=test
export DATABASE_URL=sqlite+aiosqlite:///:memory:
export REDIS_URL=redis://localhost:6379/0
export JWT_SECRET=test_secret
export OPENAI_API_KEY=test_openai_api_key
export ANTHROPIC_API_KEY=test_anthropic_api_key
export OLLAMA_URL=http://localhost:11434

# Install test dependencies if needed
pip install pytest pytest-asyncio pytest-cov aiosqlite

# Run tests with coverage
pytest tests/ -v --cov=src --cov-report=term --cov-report=html

# Print coverage report location
echo "Coverage report generated in htmlcov/ directory"
