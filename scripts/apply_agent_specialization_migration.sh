#!/bin/bash
# Apply agent specialization migration script
# This script applies the agent specialization migration to the database

# Get environment variables from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Set default values if not in .env
DB_USER=${DB_USER:-postgres}
DB_PASSWORD=${DB_PASSWORD:-postgres}
DB_NAME=${DB_NAME:-mas_framework}
# Always use localhost for the host when running outside Docker
DB_HOST=localhost
DB_PORT=${DB_PORT:-5432}

# Set PGPASSWORD environment variable for psql
export PGPASSWORD=$DB_PASSWORD

# Display migration information
echo "Applying agent specialization migration to database $DB_NAME on $DB_HOST"

# Execute the migration script
if psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f shared/database/agent_specialization_migration.sql; then
    echo -e "\e[32mMigration applied successfully\e[0m"
else
    echo -e "\e[31mError applying migration\e[0m"
    exit 1
fi
