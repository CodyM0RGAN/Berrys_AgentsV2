#!/bin/bash
# Initialize all databases with the schema from init.sql
# This script is used in the Docker setup to initialize all three databases

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

echo "Setting up multi-database environment..."

# First, run the multi-database setup script
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -f /docker-entrypoint-initdb.d/multi_db_setup.sql

echo "Initializing production database schema..."
# Apply init.sql to production database
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $PROD_DB -f /docker-entrypoint-initdb.d/init.sql

echo "Initializing development database schema..."
# Apply init.sql to development database
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DEV_DB -f /docker-entrypoint-initdb.d/init.sql

echo "Initializing test database schema..."
# Apply init.sql to test database
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $TEST_DB -f /docker-entrypoint-initdb.d/init.sql

echo "All databases initialized successfully."
