-- Migration script to add last_active_at column to agent table

-- Add last_active_at column to agent table
ALTER TABLE agent ADD COLUMN last_active_at TIMESTAMP WITH TIME ZONE;

-- Log the migration
INSERT INTO audit_log (entity_id, entity_type, action, previous_state, new_state, actor_id)
VALUES (
    gen_random_uuid(),
    'database_schema',
    'add_column',
    '{"table": "agent", "columns": ["id", "project_id", "name", "type", "configuration", "prompt_template", "status", "created_at", "updated_at", "description", "state_detail", "template_id"]}',
    '{"table": "agent", "columns": ["id", "project_id", "name", "type", "configuration", "prompt_template", "status", "created_at", "updated_at", "description", "state_detail", "template_id", "last_active_at"]}',
    NULL
);
