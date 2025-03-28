#!/bin/bash
# Run tests for the Agent Orchestrator service

echo "Running tests for Agent Orchestrator service..."

# Set environment variables for testing
export PYTHONPATH=$(dirname $(dirname $(pwd)))
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/mas_framework_test
export REDIS_URL=redis://localhost:6379/1
export JWT_SECRET=test_secret_key
export ENVIRONMENT=test

# Run pytest with coverage
python -m pytest tests/ -v --cov=src --cov-report=term --cov-report=html:coverage_report

echo "Test run complete."
