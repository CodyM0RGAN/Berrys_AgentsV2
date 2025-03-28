# PowerShell script to run tests for Agent Orchestrator service

# Set environment variables for testing
# Use absolute path for PYTHONPATH to avoid issues
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = Join-Path -Path $scriptPath -ChildPath "..\.."
$env:ENVIRONMENT = "test"
$env:DATABASE_URL = "sqlite+aiosqlite:///:memory:"
$env:REDIS_URL = "redis://localhost:6379/0"
$env:JWT_SECRET = "test_secret"
$env:MODEL_ORCHESTRATION_URL = "http://localhost:8001"

# Install test dependencies if needed
pip install pytest pytest-asyncio pytest-cov aiosqlite pydantic-settings

# Run tests with coverage
python -m pytest tests/ -v --cov=src --cov-report=term --cov-report=html

# Print coverage report location
Write-Host "Coverage report generated in htmlcov/ directory"

# Wait for user input before closing
Read-Host -Prompt "Press Enter to continue"
