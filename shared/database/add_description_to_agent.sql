-- Migration script to add description column to agent table

-- Add description column to agent table
ALTER TABLE agent ADD COLUMN description TEXT;

-- Log the migration
INSERT INTO audit_log (entity_id, entity_type, action, previous_state, new_state, actor_id)
VALUES (
    gen_random_uuid(),
    'database_schema',
    'add_column',
    '{"table": "agent", "columns": ["id", "project_id", "name", "type", "configuration", "prompt_template", "status", "created_at", "updated_at"]}',
    '{"table": "agent", "columns": ["id", "project_id", "name", "type", "configuration", "prompt_template", "status", "created_at", "updated_at", "description"]}',
    NULL
);
