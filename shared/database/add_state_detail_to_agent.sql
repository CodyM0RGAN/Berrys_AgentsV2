-- Migration script to add state_detail column to agent table

-- Add state_detail column to agent table
ALTER TABLE agent ADD COLUMN state_detail VARCHAR(20);

-- Add constraint to state_detail column
ALTER TABLE agent ADD CONSTRAINT agent_state_detail_check 
CHECK (state_detail IS NULL OR state_detail IN ('CREATED', 'INITIALIZING', 'READY', 'ACTIVE', 'PAUSED', 'ERROR', 'TERMINATED'));

-- Log the migration
INSERT INTO audit_log (entity_id, entity_type, action, previous_state, new_state, actor_id)
VALUES (
    gen_random_uuid(),
    'database_schema',
    'add_column',
    '{"table": "agent", "columns": ["id", "project_id", "name", "type", "configuration", "prompt_template", "status", "created_at", "updated_at", "description"]}',
    '{"table": "agent", "columns": ["id", "project_id", "name", "type", "configuration", "prompt_template", "status", "created_at", "updated_at", "description", "state_detail"]}',
    NULL
);
