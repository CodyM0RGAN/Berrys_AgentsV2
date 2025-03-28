# PowerShell script to run tests for Model Orchestration service

# Set environment variables for testing
# Use absolute path for PYTHONPATH to avoid issues
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = Join-Path -Path $scriptPath -ChildPath "..\.."
$env:ENVIRONMENT = "test"
$env:DATABASE_URL = "sqlite+aiosqlite:///:memory:"
$env:REDIS_URL = "redis://localhost:6379/0"
$env:JWT_SECRET = "test_secret"
$env:OPENAI_API_KEY = "test_openai_api_key"
$env:ANTHROPIC_API_KEY = "test_anthropic_api_key"
$env:OLLAMA_URL = "http://localhost:11434"

# Install test dependencies if needed
pip install pytest pytest-asyncio pytest-cov aiosqlite pydantic-settings prometheus-client tiktoken

# Run tests with coverage
python -m pytest tests/ -v --cov=src --cov-report=term --cov-report=html

# Print coverage report location
Write-Host "Coverage report generated in htmlcov/ directory"

# Wait for user input before closing
Read-Host -Prompt "Press Enter to continue"
