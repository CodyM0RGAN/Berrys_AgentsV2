@echo off
REM Run tests for Agent Orchestrator service
REM This script runs the tests and generates a coverage report

REM Set environment variables for testing
REM Use absolute path for PYTHONPATH to avoid issues
set PYTHONPATH=%~dp0..\..
set ENVIRONMENT=test
set DATABASE_URL=sqlite+aiosqlite:///:memory:
set REDIS_URL=redis://localhost:6379/0
set JWT_SECRET=test_secret
set MODEL_ORCHESTRATION_URL=http://localhost:8001

REM Install test dependencies if needed
pip install pytest pytest-asyncio pytest-cov aiosqlite pydantic-settings

REM Run tests with coverage
pytest tests/ -v --cov=src --cov-report=term --cov-report=html

REM Print coverage report location
echo Coverage report generated in htmlcov/ directory

pause
