# Multi-Database Setup Guide

This guide explains the multi-database setup for the Berrys Agents V2 project, which includes separate databases for development, testing, and production environments.

## Overview

The project uses three PostgreSQL databases within the same PostgreSQL instance:

- **mas_framework_prod**: Production database
- **mas_framework_dev**: Development database
- **mas_framework_test**: Testing database

This setup allows for:

- Isolated testing without affecting development or production data
- Development with realistic data without risking production data
- Consistent schema across all environments

## Database Initialization

The databases are initialized automatically when the PostgreSQL container starts. The initialization process:

1. Creates the three databases if they don't exist
2. Applies the schema from `init.sql` to all three databases
3. Sets up utility tables and functions for schema tracking and test data management

### Important Note on CREATE DATABASE Statements

PostgreSQL does not allow `CREATE DATABASE` statements within transaction blocks. The `multi_db_setup.sql` script handles this by:

1. Using separate transaction blocks for checking if databases exist
2. Executing `CREATE DATABASE` statements outside of any transaction using the `\gexec` meta-command
3. Connecting to each database after creation to set up utility tables

When modifying the database initialization scripts, remember:

- Never put `CREATE DATABASE` statements inside a `DO $$...$$` block
- Use the pattern in `multi_db_setup.sql` for creating databases conditionally
- Always check if a database exists before trying to create it

## Environment-Based Database Selection

Services automatically connect to the appropriate database based on the `ENVIRONMENT` environment variable:

- `ENVIRONMENT=production` → connects to `mas_framework_prod`
- `ENVIRONMENT=test` → connects to `mas_framework_test`
- `ENVIRONMENT=development` (default) → connects to `mas_framework_dev`

## Database Connection Utility

The `shared/utils/src/db_connection.py` module provides functions to get the appropriate database connection URL based on the environment:

```python
from shared.utils.src.db_connection import get_async_database_url, get_sync_database_url

# For async SQLAlchemy (FastAPI services)
async_db_url = get_async_database_url()

# For sync SQLAlchemy (Flask services)
sync_db_url = get_sync_database_url()
```

## Schema Synchronization

To ensure all databases have the same schema, use the `sync_schema.sh` script:

```bash
# Sync schema from prod to dev and test
./shared/database/sync_schema.sh
```

This script:

1. Dumps the schema from the production database
2. Applies it to the development and test databases
3. Preserves test data marked for preservation

## Data Management

### Cloning Production Data to Development

To clone data from the production database to the development database:

```bash
# Clone data from prod to dev
./shared/database/data_management.sh clone
```

### Resetting Test Database

To reset the test database to a clean state:

```bash
# Reset test database
./shared/database/data_management.sh reset
```

This preserves any test data marked for preservation.

### Marking Test Data for Preservation

To mark test data for preservation during resets:

```bash
# Mark a record for preservation
./shared/database/data_management.sh mark table_name record_id true

# Unmark a record for preservation
./shared/database/data_management.sh mark table_name record_id false
```

## Testing with the Test Database

When running tests, set the `ENVIRONMENT` environment variable to `test`:

```bash
# Linux/macOS
ENVIRONMENT=test pytest

# Windows PowerShell
$env:ENVIRONMENT="test"; pytest

# Windows Command Prompt
set ENVIRONMENT=test
pytest
```

The test database is automatically used for all database operations.

## Best Practices

1. **Always use the database connection utility** to get database URLs, rather than hardcoding them.
2. **Run tests against the test database** to avoid affecting development or production data.
3. **Sync schemas after migrations** to ensure all environments have the same schema.
4. **Mark important test data for preservation** to avoid having to recreate it after resets.
5. **Clone production data to development** when you need realistic data for development.
