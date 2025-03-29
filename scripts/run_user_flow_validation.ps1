# This script runs the user flow validation tests to verify system integration

# Create logs directory if it doesn't exist
if (-not (Test-Path -Path "logs")) {
    New-Item -Path "logs" -ItemType Directory | Out-Null
    Write-Host "Created logs directory"
}

# Set environment variables for service endpoints
$env:API_GATEWAY_URL = "http://localhost:8000"
$env:PROJECT_COORDINATOR_URL = "http://localhost:8005"
$env:AGENT_ORCHESTRATOR_URL = "http://localhost:8001"
$env:MODEL_ORCHESTRATION_URL = "http://localhost:8003"
$env:WEB_DASHBOARD_URL = "http://localhost:5000"

Write-Host "=================================="
Write-Host "Starting user flow validation..."
Write-Host "=================================="
Write-Host ""

# Run the user flow validation script
try {
    python scripts/test_user_flows.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "User flow validation completed successfully."
        exit 0
    } else {
        Write-Host "User flow validation failed. Check the logs for details."
        exit 1
    }
} catch {
    Write-Host "Error executing user flow validation script: $_"
    exit 1
}
