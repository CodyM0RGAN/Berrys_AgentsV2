-- Update enum constraints to uppercase

-- First, drop all existing constraints

-- Drop project.status constraint
ALTER TABLE project DROP CONSTRAINT IF EXISTS project_status_check;

-- Drop agent.status constraint
ALTER TABLE agent DROP CONSTRAINT IF EXISTS agent_status_check;

-- Drop agent.type constraint
ALTER TABLE agent DROP CONSTRAINT IF EXISTS agent_type_check;

-- Drop task.status constraint
ALTER TABLE task DROP CONSTRAINT IF EXISTS task_status_check;

-- Drop task.priority constraint
ALTER TABLE task DROP CONSTRAINT IF EXISTS task_priority_check;

-- Drop tool.integration_type constraint
ALTER TABLE tool DROP CONSTRAINT IF EXISTS tool_integration_type_check;

-- Drop tool.status constraint
ALTER TABLE tool DROP CONSTRAINT IF EXISTS tool_status_check;

-- Now update existing data to use uppercase values

-- Update project.status values to uppercase
UPDATE project SET status = UPPER(status) WHERE status IS NOT NULL;

-- Update agent.status values to uppercase
UPDATE agent SET status = UPPER(status) WHERE status IS NOT NULL;

-- Update agent.type values to uppercase
UPDATE agent SET type = UPPER(type) WHERE type IS NOT NULL;

-- Update task.status values to uppercase
UPDATE task SET status = UPPER(status) WHERE status IS NOT NULL;

-- Skip task.priority as it's an integer, not a string
-- UPDATE task SET priority = UPPER(priority) WHERE priority IS NOT NULL;

-- Update tool.integration_type values to uppercase
UPDATE tool SET integration_type = UPPER(integration_type) WHERE integration_type IS NOT NULL;

-- Update tool.status values to uppercase
UPDATE tool SET status = UPPER(status) WHERE status IS NOT NULL;

-- Finally, add the new constraints with uppercase values

-- Add project.status constraint
ALTER TABLE project ADD CONSTRAINT project_status_check CHECK (status IN ('DRAFT', 'PLANNING', 'IN_PROGRESS', 'REVIEW', 'COMPLETED', 'ARCHIVED', 'CANCELLED'));

-- Add agent.status constraint
ALTER TABLE agent ADD CONSTRAINT agent_status_check CHECK (status IN ('INACTIVE', 'ACTIVE', 'BUSY', 'ERROR', 'MAINTENANCE'));

-- Add agent.type constraint
ALTER TABLE agent ADD CONSTRAINT agent_type_check CHECK (type IN ('COORDINATOR', 'ASSISTANT', 'RESEARCHER', 'DEVELOPER', 'DESIGNER', 'SPECIALIST', 'AUDITOR', 'CUSTOM'));

-- Add task.status constraint
ALTER TABLE task ADD CONSTRAINT task_status_check CHECK (status IN ('PENDING', 'ASSIGNED', 'IN_PROGRESS', 'BLOCKED', 'COMPLETED', 'FAILED', 'CANCELLED'));

-- Add task.priority constraint with integer values (1=LOW, 2=MEDIUM, 3=HIGH, 4=CRITICAL)
ALTER TABLE task ADD CONSTRAINT task_priority_check CHECK (priority IN (1, 2, 3, 4));

-- Add tool.integration_type constraint
ALTER TABLE tool ADD CONSTRAINT tool_integration_type_check CHECK (integration_type IN ('API', 'CLI', 'LIBRARY', 'SERVICE', 'CUSTOM'));

-- Add tool.status constraint
ALTER TABLE tool ADD CONSTRAINT tool_status_check CHECK (status IN ('ACTIVE', 'INACTIVE', 'DEPRECATED', 'EXPERIMENTAL'));
