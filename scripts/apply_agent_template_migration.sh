#!/bin/bash
# Apply Agent Template Migration Script
# This script applies the agent_template_migration.sql script to the database.

# Exit on error
set -e

# Set the current directory to the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Get the project root directory
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Set the path to the migration script
MIGRATION_SCRIPT_PATH="$PROJECT_ROOT/shared/database/agent_template_migration.sql"

# Check if the migration script exists
if [ ! -f "$MIGRATION_SCRIPT_PATH" ]; then
    echo "Error: Migration script not found at $MIGRATION_SCRIPT_PATH"
    exit 1
fi

# Load environment variables from .env file
ENV_FILE="$PROJECT_ROOT/.env"
if [ -f "$ENV_FILE" ]; then
    echo "Loading environment variables from .env file..."
    # Export variables from .env file
    export $(grep -v '^#' "$ENV_FILE" | xargs)
fi

# Validate required environment variables
if [ -z "$DB_HOST" ] || [ -z "$DB_PORT" ] || [ -z "$DB_NAME" ] || [ -z "$DB_USER" ] || [ -z "$DB_PASSWORD" ]; then
    echo "Error: Missing required database environment variables. Please check your .env file."
    echo "Required variables: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD"
    exit 1
fi

# If DB_HOST is "postgres" (Docker service name), use "localhost" for local execution
if [ "$DB_HOST" = "postgres" ]; then
    echo "Converting Docker service name 'postgres' to 'localhost' for local execution..."
    DB_HOST="localhost"
fi

echo "Using database connection: $DB_HOST:$DB_PORT/$DB_NAME"

# Apply the migration script
echo "Applying Agent Template migration script to database $DB_NAME on $DB_HOST..."

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo "Error: psql command not found. Please ensure PostgreSQL is installed and added to your PATH."
    exit 1
fi

# Apply the migration script using psql
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -U "$DB_USER" -f "$MIGRATION_SCRIPT_PATH"

if [ $? -ne 0 ]; then
    echo "Error: Failed to apply migration script."
    exit 1
fi

echo "Migration script applied successfully."

# Return to the original directory
cd "$PROJECT_ROOT"

echo "Agent Template migration completed successfully."
