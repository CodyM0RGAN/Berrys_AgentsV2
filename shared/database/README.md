# Database Management

This directory contains scripts and SQL files for managing the PostgreSQL database used by the Berrys Agents V2 project.

## Multi-Database Setup

The project uses three PostgreSQL databases within the same PostgreSQL instance:

- **mas_framework_prod**: Production database
- **mas_framework_dev**: Development database
- **mas_framework_test**: Testing database

This setup allows for isolated testing, development with realistic data, and consistent schema across all environments.

## Files

- **init.sql**: The main database schema definition
- **multi_db_setup.sql**: Script to create the three databases and set up utility tables
- **init_all_dbs.sh**: Script to initialize all three databases with the schema
- **sync_schema.sh**: Script to synchronize schema from prod to dev and test
- **data_management.sh**: Script for managing data across the databases
- **data_management.bat**: Windows version of the data management script
- **enum_standardization_postgres.sql**: SQL for standardizing enums
- **schema_standardization_postgres.sql**: SQL for standardizing schema

## Usage

### Database Initialization

The databases are initialized automatically when the PostgreSQL container starts. The initialization process:

1. Creates the three databases if they don't exist
2. Applies the schema from `init.sql` to all three databases
3. Sets up utility tables and functions for schema tracking and test data management

### Schema Synchronization

To ensure all databases have the same schema, use the `sync_schema.sh` script:

```bash
# Sync schema from prod to dev and test
./sync_schema.sh
```

### Data Management

#### Cloning Production Data to Development

To clone data from the production database to the development database:

```bash
# Clone data from prod to dev
./data_management.sh clone
```

#### Resetting Test Database

To reset the test database to a clean state:

```bash
# Reset test database
./data_management.sh reset
```

#### Marking Test Data for Preservation

To mark test data for preservation during resets:

```bash
# Mark a record for preservation
./data_management.sh mark table_name record_id true

# Unmark a record for preservation
./data_management.sh mark table_name record_id false
```

## Further Reading

For more information about the multi-database setup, see the [Multi-Database Setup Guide](../../docs/best-practices/multi-database-setup.md).
