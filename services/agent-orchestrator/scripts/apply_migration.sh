#!/bin/bash
# Script to apply the Agent Orchestrator service migrations

# Change to the script directory
cd "$(dirname "$0")"

# Run the migration script
python apply_migration.py "$@"

# Check the exit code
if [ $? -ne 0 ]; then
    echo "Migration failed with exit code $?"
    exit 1
fi

echo "Migration completed successfully"
exit 0
