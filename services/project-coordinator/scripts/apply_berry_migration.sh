#!/bin/bash
# Script to apply the Berry agent configuration migration on Unix-based systems

echo "Applying Berry agent configuration migration..."
python "$(dirname "$0")/apply_berry_migration.py" "$@"

if [ $? -eq 0 ]; then
    echo "Migration completed successfully."
else
    echo "Migration failed with error code $?."
    exit 1
fi
