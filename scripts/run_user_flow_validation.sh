#!/bin/bash
# This script runs the user flow validation tests to verify system integration

# Set strict error handling
set -e

# Create logs directory if it doesn't exist
mkdir -p logs

# Set environment variables for service endpoints
export API_GATEWAY_URL=http://localhost:8000
export PROJECT_COORDINATOR_URL=http://localhost:8005
export AGENT_ORCHESTRATOR_URL=http://localhost:8001
export MODEL_ORCHESTRATION_URL=http://localhost:8003
export WEB_DASHBOARD_URL=http://localhost:5000

# Make the test script executable
chmod +x scripts/test_user_flows.py

echo "=================================="
echo "Starting user flow validation..."
echo "=================================="
echo

# Run the user flow validation script
python scripts/test_user_flows.py

# Check the exit code
if [ $? -eq 0 ]; then
    echo "User flow validation completed successfully."
    exit 0
else
    echo "User flow validation failed. Check the logs for details."
    exit 1
fi
