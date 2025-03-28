-- =============================================
-- DATABASE SCHEMA STANDARDIZATION SCRIPT (PostgreSQL)
-- =============================================
-- This script standardizes the database schema by:
-- 1. Renaming plural tables to singular form
-- 2. Updating foreign key references
-- 3. Adding missing metadata columns
-- 
-- Each operation includes a commented rollback command
-- =============================================

-- Start transaction to ensure all changes are atomic
BEGIN;

-- =============================================
-- TABLE RENAMING (PLURAL TO SINGULAR)
-- =============================================

-- Rename agent_tools to agent_tool
ALTER TABLE IF EXISTS agent_tools RENAME TO agent_tool;
-- ROLLBACK: ALTER TABLE agent_tool RENAME TO agent_tools;

-- Rename models to model
ALTER TABLE IF EXISTS models RENAME TO model;
-- ROLLBACK: ALTER TABLE model RENAME TO models;

-- Rename requests to request
ALTER TABLE IF EXISTS requests RENAME TO request;
-- ROLLBACK: ALTER TABLE request RENAME TO requests;

-- Rename provider_quotas to provider_quota
ALTER TABLE IF EXISTS provider_quotas RENAME TO provider_quota;
-- ROLLBACK: ALTER TABLE provider_quota RENAME TO provider_quotas;

-- Rename task_dependencies to task_dependency
ALTER TABLE IF EXISTS task_dependencies RENAME TO task_dependency;
-- ROLLBACK: ALTER TABLE task_dependency RENAME TO task_dependencies;

-- =============================================
-- FOREIGN KEY REFERENCE UPDATES
-- =============================================

-- Update foreign keys for agent_tool (previously agent_tools)
-- Note: This is only needed if the constraint names change with the table rename
-- If PostgreSQL automatically updates the constraint names, these may not be needed

-- Update foreign keys for model (previously models)
-- Note: This is only needed if the constraint names change with the table rename

-- Update foreign keys for request (previously requests)
-- Note: This is only needed if the constraint names change with the table rename

-- Update foreign keys for provider_quota (previously provider_quotas)
-- Note: This is only needed if the constraint names change with the table rename

-- Update foreign keys for task_dependency (previously task_dependencies)
-- Note: This is only needed if the constraint names change with the table rename

-- =============================================
-- MISSING METADATA COLUMNS
-- =============================================

-- Add tool_metadata column to tool table
ALTER TABLE IF EXISTS tool ADD COLUMN IF NOT EXISTS tool_metadata JSONB DEFAULT '{}';
-- ROLLBACK: ALTER TABLE tool DROP COLUMN tool_metadata;

-- Update existing rows to have an empty JSON object as tool_metadata
UPDATE tool SET tool_metadata = '{}' WHERE tool_metadata IS NULL;

-- =============================================
-- VERIFY CHANGES
-- =============================================

-- List all tables to verify renames
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';

-- Verify tool_metadata column was added
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'tool' AND column_name = 'tool_metadata';

-- Commit the transaction if everything is successful
COMMIT;

-- =============================================
-- ROLLBACK ENTIRE TRANSACTION
-- =============================================
-- If you need to rollback all changes, you can use:
-- ROLLBACK;
