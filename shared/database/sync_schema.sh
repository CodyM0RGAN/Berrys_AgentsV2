#!/bin/bash
# Schema synchronization script for multi-environment PostgreSQL databases
# This script synchronizes the schema from prod to dev and test databases

set -e

# Database connection parameters
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_USER=${DB_USER:-postgres}
DB_PASSWORD=${DB_PASSWORD:-postgres}
PROD_DB=${PROD_DB:-mas_framework_prod}
DEV_DB=${DEV_DB:-mas_framework_dev}
TEST_DB=${TEST_DB:-mas_framework_test}

# Export password for psql
export PGPASSWORD=$DB_PASSWORD

echo "Starting schema synchronization..."

# Dump schema from production database
echo "Dumping schema from $PROD_DB..."
pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $PROD_DB --schema-only -f /tmp/schema_dump.sql

# Apply schema to development database
echo "Applying schema to $DEV_DB..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DEV_DB -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DEV_DB -f /tmp/schema_dump.sql

# Apply schema to test database
echo "Applying schema to $TEST_DB..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $TEST_DB -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $TEST_DB -f /tmp/schema_dump.sql

# Clean up
rm /tmp/schema_dump.sql

echo "Schema synchronization completed successfully."
