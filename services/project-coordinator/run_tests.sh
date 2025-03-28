#!/bin/bash

# Run tests for the Project Coordinator service
# This script runs the tests for the Project Coordinator service

# Set up environment variables
PROJECT_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
export PYTHONPATH=$PYTHONPATH:$(pwd):$PROJECT_ROOT
export ENVIRONMENT=test

# Run the tests
pytest tests/ -v
