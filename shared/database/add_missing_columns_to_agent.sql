-- Comprehensive migration script to add all missing columns to agent table

-- Add description column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'agent' AND column_name = 'description'
    ) THEN
        ALTER TABLE agent ADD COLUMN description TEXT;
    END IF;
END $$;

-- Add state_detail column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'agent' AND column_name = 'state_detail'
    ) THEN
        ALTER TABLE agent ADD COLUMN state_detail VARCHAR(20);
        
        -- Add constraint to state_detail column
        ALTER TABLE agent ADD CONSTRAINT agent_state_detail_check 
        CHECK (state_detail IS NULL OR state_detail IN ('CREATED', 'INITIALIZING', 'READY', 'ACTIVE', 'PAUSED', 'ERROR', 'TERMINATED'));
    END IF;
END $$;

-- Add template_id column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'agent' AND column_name = 'template_id'
    ) THEN
        ALTER TABLE agent ADD COLUMN template_id VARCHAR;
    END IF;
END $$;

-- Add last_active_at column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'agent' AND column_name = 'last_active_at'
    ) THEN
        ALTER TABLE agent ADD COLUMN last_active_at TIMESTAMP WITH TIME ZONE;
    END IF;
END $$;

-- Log the migration
INSERT INTO audit_log (id, entity_id, entity_type, action, previous_state, new_state, actor_id)
VALUES (
    gen_random_uuid(),
    gen_random_uuid(),
    'database_schema',
    'add_columns',
    '{"table": "agent", "columns": ["id", "project_id", "name", "type", "configuration", "prompt_template", "status", "created_at", "updated_at"]}',
    '{"table": "agent", "columns": ["id", "project_id", "name", "type", "configuration", "prompt_template", "status", "created_at", "updated_at", "description", "state_detail", "template_id", "last_active_at"]}',
    NULL
);
