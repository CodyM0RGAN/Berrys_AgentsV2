-- Multi-environment PostgreSQL database setup script
-- This script creates three databases: prod, dev, and test
-- It does not modify any table definitions

-- Check if mas_framework exists (default name from docker-compose)
DO $$
DECLARE
    db_exists BOOLEAN;
BEGIN
    SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname = 'mas_framework') INTO db_exists;
    
    IF db_exists THEN
        -- If mas_framework exists, rename it to mas_framework_prod
        RAISE NOTICE 'Renaming mas_framework to mas_framework_prod...';
        -- We need to terminate all connections to the database before renaming
        PERFORM pg_terminate_backend(pid) 
        FROM pg_stat_activity 
        WHERE datname = 'mas_framework' AND pid <> pg_backend_pid();
        
        EXECUTE 'ALTER DATABASE mas_framework RENAME TO mas_framework_prod';
        RAISE NOTICE 'Database renamed to mas_framework_prod';
    END IF;
END
$$;

-- Check if mas_framework_prod exists
DO $$
DECLARE
    db_exists BOOLEAN;
BEGIN
    SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname = 'mas_framework_prod') INTO db_exists;
    
    IF NOT db_exists THEN
        RAISE NOTICE 'mas_framework_prod database does not exist';
    ELSE
        RAISE NOTICE 'mas_framework_prod database already exists';
    END IF;
END
$$;

-- Create production database if it doesn't exist
-- This must be outside of any transaction block
SELECT 'CREATE DATABASE mas_framework_prod' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'mas_framework_prod')\gexec

-- Check if mas_framework_dev exists
DO $$
DECLARE
    db_exists BOOLEAN;
BEGIN
    SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname = 'mas_framework_dev') INTO db_exists;
    
    IF NOT db_exists THEN
        RAISE NOTICE 'mas_framework_dev database does not exist';
    ELSE
        RAISE NOTICE 'mas_framework_dev database already exists';
    END IF;
END
$$;

-- Create development database if it doesn't exist
-- This must be outside of any transaction block
SELECT 'CREATE DATABASE mas_framework_dev' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'mas_framework_dev')\gexec

-- Check if mas_framework_test exists
DO $$
DECLARE
    db_exists BOOLEAN;
BEGIN
    SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname = 'mas_framework_test') INTO db_exists;
    
    IF NOT db_exists THEN
        RAISE NOTICE 'mas_framework_test database does not exist';
    ELSE
        RAISE NOTICE 'mas_framework_test database already exists';
    END IF;
END
$$;

-- Create test database if it doesn't exist
-- This must be outside of any transaction block
SELECT 'CREATE DATABASE mas_framework_test' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'mas_framework_test')\gexec

-- Create test data tracking table in each database

-- Connect to the production database
\c mas_framework_prod;

-- Create test data tracking table if it doesn't exist
CREATE TABLE IF NOT EXISTS test_data_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name VARCHAR(100) NOT NULL,
    record_id UUID NOT NULL,
    preserve_in_reset BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(table_name, record_id)
);

-- Create schema version tracking table if it doesn't exist
CREATE TABLE IF NOT EXISTS schema_version (
    id SERIAL PRIMARY KEY,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Connect to the development database
\c mas_framework_dev;

-- Create test data tracking table if it doesn't exist
CREATE TABLE IF NOT EXISTS test_data_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name VARCHAR(100) NOT NULL,
    record_id UUID NOT NULL,
    preserve_in_reset BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(table_name, record_id)
);

-- Create schema version tracking table if it doesn't exist
CREATE TABLE IF NOT EXISTS schema_version (
    id SERIAL PRIMARY KEY,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Connect to the test database
\c mas_framework_test;

-- Create test data tracking table if it doesn't exist
CREATE TABLE IF NOT EXISTS test_data_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name VARCHAR(100) NOT NULL,
    record_id UUID NOT NULL,
    preserve_in_reset BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(table_name, record_id)
);

-- Create schema version tracking table if it doesn't exist
CREATE TABLE IF NOT EXISTS schema_version (
    id SERIAL PRIMARY KEY,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create utility functions for marking test data for preservation
CREATE OR REPLACE FUNCTION mark_test_data_preserve(p_table_name text, p_record_id uuid, p_preserve boolean)
RETURNS void AS $$
BEGIN
    INSERT INTO test_data_tracking (table_name, record_id, preserve_in_reset)
    VALUES (p_table_name, p_record_id, p_preserve)
    ON CONFLICT (table_name, record_id) 
    DO UPDATE SET preserve_in_reset = p_preserve;
END;
$$ LANGUAGE plpgsql;
