"""
Model structure alignment migration.

This migration script aligns the model structure across all services,
ensuring consistent field definitions and metadata column handling.

Revision ID: 04_model_structure_alignment
Revises: 03_add_tool_metadata_column
Create Date: 2025-03-25 16:40:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid
from datetime import datetime

# revision identifiers, used by Alembic
revision = '04_model_structure_alignment'
down_revision = '03_add_tool_metadata_column'
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade the database schema."""
    # Standardize JSON columns to use JSONB
    op.execute("""
    -- Convert JSON columns to JSONB
    ALTER TABLE project ALTER COLUMN project_metadata TYPE JSONB USING project_metadata::jsonb;
    ALTER TABLE agent ALTER COLUMN agent_metadata TYPE JSONB USING agent_metadata::jsonb;
    ALTER TABLE tool ALTER COLUMN tool_metadata TYPE JSONB USING tool_metadata::jsonb;
    ALTER TABLE task ALTER COLUMN task_metadata TYPE JSONB USING task_metadata::jsonb;
    ALTER TABLE model ALTER COLUMN model_metadata TYPE JSONB USING model_metadata::jsonb;
    
    -- Set default empty JSON object for metadata columns
    ALTER TABLE project ALTER COLUMN project_metadata SET DEFAULT '{}'::jsonb;
    ALTER TABLE agent ALTER COLUMN agent_metadata SET DEFAULT '{}'::jsonb;
    ALTER TABLE tool ALTER COLUMN tool_metadata SET DEFAULT '{}'::jsonb;
    ALTER TABLE task ALTER COLUMN task_metadata SET DEFAULT '{}'::jsonb;
    ALTER TABLE model ALTER COLUMN model_metadata SET DEFAULT '{}'::jsonb;
    """)
    
    # Add any missing metadata columns
    op.execute("""
    -- Add metadata columns to tables that don't have them
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name = 'user' AND column_name = 'user_metadata') THEN
            ALTER TABLE "user" ADD COLUMN user_metadata JSONB DEFAULT '{}'::jsonb;
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name = 'human_interaction' AND column_name = 'interaction_metadata') THEN
            ALTER TABLE human_interaction ADD COLUMN interaction_metadata JSONB DEFAULT '{}'::jsonb;
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name = 'audit_log' AND column_name = 'audit_metadata') THEN
            ALTER TABLE audit_log ADD COLUMN audit_metadata JSONB DEFAULT '{}'::jsonb;
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
