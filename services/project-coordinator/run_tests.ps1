# Run tests for the Project Coordinator service
# This script runs the tests for the Project Coordinator service

# Set up environment variables
$projectRoot = (Get-Item (Get-Location)).Parent.Parent.FullName
$env:PYTHONPATH = "$env:PYTHONPATH;$(Get-Location);$projectRoot"
$env:ENVIRONMENT = "test"

# Run the tests
pytest tests/ -v
