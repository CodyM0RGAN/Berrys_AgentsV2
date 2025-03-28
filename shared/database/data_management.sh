#!/bin/bash
# Data management script for multi-environment PostgreSQL databases
# This script provides functions for cloning data and resetting test database

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

# Function to clone data from prod to dev
clone_prod_to_dev() {
    echo "Starting data clone from $PROD_DB to $DEV_DB..."
    
    # Get list of tables
    TABLES=$(psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $PROD_DB -t -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename != 'schema_version' AND tablename != 'test_data_tracking';")
    
    # For each table, copy data
    for TABLE in $TABLES; do
        echo "Copying data for table: $TABLE"
        
        # Clear table in dev
        psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DEV_DB -c "TRUNCATE TABLE $TABLE CASCADE;"
        
        # Copy data from prod to dev
        pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $PROD_DB --table=$TABLE --data-only | psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DEV_DB
    done
    
    echo "Data clone completed successfully."
}

# Function to reset test database
reset_test_db() {
    echo "Resetting test database $TEST_DB..."
    
    # Get list of tables
    TABLES=$(psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $TEST_DB -t -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename != 'schema_version' AND tablename != 'test_data_tracking';")
    
    # For each table, clear data except preserved test data
    for TABLE in $TABLES; do
        echo "Resetting data for table: $TABLE"
        
        # Get list of preserved record IDs
        PRESERVED_IDS=$(psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $TEST_DB -t -c "SELECT record_id FROM test_data_tracking WHERE table_name = '$TABLE' AND preserve_in_reset = true;")
        
        if [ -z "$PRESERVED_IDS" ]; then
            # No preserved records, truncate the table
            psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $TEST_DB -c "TRUNCATE TABLE $TABLE CASCADE;"
        else
            # Delete all records except preserved ones
            ID_LIST=$(echo $PRESERVED_IDS | tr '\n' ',' | sed 's/,$//')
            psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $TEST_DB -c "DELETE FROM $TABLE WHERE id NOT IN ($ID_LIST);"
        fi
    done
    
    # Insert default data
    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $TEST_DB -c "
        -- Insert default admin user if not exists
        INSERT INTO users (username, email, password_hash, is_admin)
        VALUES ('test_admin', 'test_admin@example.com', '\$2b\$12\$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', TRUE)
        ON CONFLICT (username) DO NOTHING;
    "
    
    echo "Test database reset completed successfully."
}

# Function to mark test data for preservation
mark_test_data() {
    TABLE=$1
    RECORD_ID=$2
    PRESERVE=$3
    
    if [ "$PRESERVE" = "true" ]; then
        PRESERVE_VAL="true"
    else
        PRESERVE_VAL="false"
    fi
    
    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $TEST_DB -c "
        SELECT mark_test_data_preserve('$TABLE', '$RECORD_ID', $PRESERVE_VAL);
    "
    
    echo "Marked record $RECORD_ID in table $TABLE with preserve=$PRESERVE_VAL"
}

# Main execution based on command line arguments
if [ $# -eq 0 ]; then
    echo "Usage: $0 [clone|reset|mark] [args...]"
    echo "  clone - Clone data from prod to dev"
    echo "  reset - Reset test database"
    echo "  mark table_name record_id [true|false] - Mark test data for preservation"
    exit 1
fi

COMMAND=$1
shift

case $COMMAND in
    clone)
        clone_prod_to_dev
        ;;
    reset)
        reset_test_db
        ;;
    mark)
        if [ $# -lt 2 ]; then
            echo "Usage: $0 mark table_name record_id [true|false]"
            exit 1
        fi
        TABLE=$1
        RECORD_ID=$2
        PRESERVE=${3:-true}
        mark_test_data $TABLE $RECORD_ID $PRESERVE
        ;;
    *)
        echo "Unknown command: $COMMAND"
        echo "Usage: $0 [clone|reset|mark] [args...]"
        exit 1
        ;;
esac

exit 0
