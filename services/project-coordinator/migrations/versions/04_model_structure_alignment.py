"""
Model structure alignment migration.

This migration script aligns the model structure across all services,
ensuring consistent field definitions and metadata column handling.

Specifically, this migration:
1. Converts JSON columns to JSONB for better performance and functionality
2. Sets default empty JSON objects for metadata columns
3. Adds metadata columns to tables that don't have them
4. Ensures all tables have created_at and updated_at columns
5. Creates triggers to automatically update the updated_at column

Revision ID: 04_model_structure_alignment
Revises: 03_create_agent_tables
Create Date: 2025-03-25 16:41:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid
from datetime import datetime

# revision identifiers, used by Alembic
revision = '04_model_structure_alignment'
down_revision = '03_create_agent_tables'
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade the database schema."""
    # Standardize JSON columns to use JSONB
    op.execute("""
    -- Convert JSON columns to JSONB
    ALTER TABLE project ALTER COLUMN project_metadata TYPE JSONB USING project_metadata::jsonb;
    ALTER TABLE project_resource ALTER COLUMN resource_metadata TYPE JSONB USING resource_metadata::jsonb;
    ALTER TABLE project_artifact ALTER COLUMN artifact_metadata TYPE JSONB USING artifact_metadata::jsonb;
    ALTER TABLE chat_session ALTER COLUMN session_metadata TYPE JSONB USING session_metadata::jsonb;
    ALTER TABLE chat_message ALTER COLUMN message_metadata TYPE JSONB USING message_metadata::jsonb;
    
    -- Set default empty JSON object for metadata columns
    ALTER TABLE project ALTER COLUMN project_metadata SET DEFAULT '{}'::jsonb;
    ALTER TABLE project_resource ALTER COLUMN resource_metadata SET DEFAULT '{}'::jsonb;
    ALTER TABLE project_artifact ALTER COLUMN artifact_metadata SET DEFAULT '{}'::jsonb;
    ALTER TABLE chat_session ALTER COLUMN session_metadata SET DEFAULT '{}'::jsonb;
    ALTER TABLE chat_message ALTER COLUMN message_metadata SET DEFAULT '{}'::jsonb;
    """)
    
    # Add any missing metadata columns
    op.execute("""
    -- Add metadata columns to tables that don't have them
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name = 'project_state' AND column_name = 'state_metadata') THEN
            ALTER TABLE project_state ADD COLUMN state_metadata JSONB DEFAULT '{}'::jsonb;
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name = 'project_progress' AND column_name = 'progress_metadata') THEN
            ALTER TABLE project_progress ADD COLUMN progress_metadata JSONB DEFAULT '{}'::jsonb;
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name = 'project_analytic' AND column_name = 'analytic_metadata') THEN
            ALTER TABLE project_analytic ADD COLUMN analytic_metadata JSONB DEFAULT '{}'::jsonb;
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name = 'agent_instruction' AND column_name = 'instruction_metadata') THEN
            ALTER TABLE agent_instruction ADD COLUMN instruction_metadata JSONB DEFAULT '{}'::jsonb;
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name = 'agent_capability' AND column_name = 'capability_metadata') THEN
            ALTER TABLE agent_capability ADD COLUMN capability_metadata JSONB DEFAULT '{}'::jsonb;
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name = 'agent_knowledge_domain' AND column_name = 'domain_metadata') THEN
            ALTER TABLE agent_knowledge_domain ADD COLUMN domain_metadata JSONB DEFAULT '{}'::jsonb;
        END IF;
    END
    $$;
    """)
    
    # Ensure all tables have consistent timestamp columns
    op.execute("""
    -- Ensure all tables have created_at and updated_at columns
    DO $$
    DECLARE
        table_name text;
    BEGIN
        FOR table_name IN 
            SELECT t.table_name 
            FROM information_schema.tables t
            WHERE t.table_schema = 'public' 
            AND t.table_type = 'BASE TABLE'
        LOOP
            -- Add created_at if it doesn't exist
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name = table_name AND column_name = 'created_at') THEN
                EXECUTE format('ALTER TABLE %I ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL', table_name);
            END IF;
            
            -- Add updated_at if it doesn't exist
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name = table_name AND column_name = 'updated_at') THEN
                EXECUTE format('ALTER TABLE %I ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL', table_name);
            END IF;
            
            -- Add trigger to update updated_at automatically
            EXECUTE format('
                DROP TRIGGER IF EXISTS update_timestamp ON %I;
                CREATE TRIGGER update_timestamp
                BEFORE UPDATE ON %I
                FOR EACH ROW
                EXECUTE FUNCTION update_timestamp();
            ', table_name, table_name);
        END LOOP;
    END
    $$;
    
    -- Create update_timestamp function if it doesn't exist
    CREATE OR REPLACE FUNCTION update_timestamp()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = now();
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)


def downgrade():
    """Downgrade the database schema."""
    # This is a non-destructive migration, so we don't need to do anything for downgrade
    pass
