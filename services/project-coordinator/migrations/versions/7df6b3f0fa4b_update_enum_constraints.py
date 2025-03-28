"""Update enum constraints to uppercase

Revision ID: 7df6b3f0fa4b
Revises: 9fdeb4ad4a17
Create Date: 2025-03-26 13:20:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '7df6b3f0fa4b'
down_revision = '9fdeb4ad4a17'
branch_labels = None
depends_on = None


def upgrade():
    # First, drop all existing constraints
    
    # Drop project.status constraint
    op.execute("ALTER TABLE project DROP CONSTRAINT IF EXISTS project_status_check")
    
    # Drop agent.status constraint
    op.execute("ALTER TABLE agent DROP CONSTRAINT IF EXISTS agent_status_check")
    
    # Drop agent.type constraint
    op.execute("ALTER TABLE agent DROP CONSTRAINT IF EXISTS agent_type_check")
    
    # Drop task.status constraint
    op.execute("ALTER TABLE task DROP CONSTRAINT IF EXISTS task_status_check")
    
    # Drop task.priority constraint
    op.execute("ALTER TABLE task DROP CONSTRAINT IF EXISTS task_priority_check")
    
    # Drop tool.integration_type constraint
    op.execute("ALTER TABLE tool DROP CONSTRAINT IF EXISTS tool_integration_type_check")
    
    # Drop tool.status constraint
    op.execute("ALTER TABLE tool DROP CONSTRAINT IF EXISTS tool_status_check")
    
    # Now update existing data to use uppercase values
    
    # Update project.status values to uppercase
    op.execute("UPDATE project SET status = UPPER(status) WHERE status IS NOT NULL")
    
    # Update agent.status values to uppercase
    op.execute("UPDATE agent SET status = UPPER(status) WHERE status IS NOT NULL")
    
    # Update agent.type values to uppercase
    op.execute("UPDATE agent SET type = UPPER(type) WHERE type IS NOT NULL")
    
    # Update task.status values to uppercase
    op.execute("UPDATE task SET status = UPPER(status) WHERE status IS NOT NULL")
    
    # Skip task.priority as it's an integer, not a string
    # op.execute("UPDATE task SET priority = UPPER(priority) WHERE priority IS NOT NULL")
    
    # Update tool.integration_type values to uppercase
    op.execute("UPDATE tool SET integration_type = UPPER(integration_type) WHERE integration_type IS NOT NULL")
    
    # Update tool.status values to uppercase
    op.execute("UPDATE tool SET status = UPPER(status) WHERE status IS NOT NULL")
    
    # Finally, add the new constraints with uppercase values
    
    # Add project.status constraint
    op.execute("ALTER TABLE project ADD CONSTRAINT project_status_check CHECK (status IN ('DRAFT', 'PLANNING', 'IN_PROGRESS', 'REVIEW', 'COMPLETED', 'ARCHIVED', 'CANCELLED'))")

    # Add agent.status constraint
    op.execute("ALTER TABLE agent ADD CONSTRAINT agent_status_check CHECK (status IN ('INACTIVE', 'ACTIVE', 'BUSY', 'ERROR', 'MAINTENANCE'))")

    # Add agent.type constraint
    op.execute("ALTER TABLE agent ADD CONSTRAINT agent_type_check CHECK (type IN ('COORDINATOR', 'ASSISTANT', 'RESEARCHER', 'DEVELOPER', 'DESIGNER', 'SPECIALIST', 'AUDITOR', 'CUSTOM'))")

    # Add task.status constraint
    op.execute("ALTER TABLE task ADD CONSTRAINT task_status_check CHECK (status IN ('PENDING', 'ASSIGNED', 'IN_PROGRESS', 'BLOCKED', 'COMPLETED', 'FAILED', 'CANCELLED'))")

    # Add task.priority constraint with integer values (1=LOW, 2=MEDIUM, 3=HIGH, 4=CRITICAL)
    op.execute("ALTER TABLE task ADD CONSTRAINT task_priority_check CHECK (priority IN (1, 2, 3, 4))")

    # Add tool.integration_type constraint
    op.execute("ALTER TABLE tool ADD CONSTRAINT tool_integration_type_check CHECK (integration_type IN ('API', 'CLI', 'LIBRARY', 'SERVICE', 'CUSTOM'))")

    # Add tool.status constraint
    op.execute("ALTER TABLE tool ADD CONSTRAINT tool_status_check CHECK (status IN ('ACTIVE', 'INACTIVE', 'DEPRECATED', 'EXPERIMENTAL'))")


def downgrade():
    # Downgrade check constraint to project.status
    op.execute("ALTER TABLE project DROP CONSTRAINT IF EXISTS project_status_check")
    op.execute("ALTER TABLE project ADD CONSTRAINT project_status_check CHECK (status IN ('draft', 'planning', 'in_progress', 'review', 'completed', 'archived', 'cancelled'))")

    # Downgrade check constraint to agent.status
    op.execute("ALTER TABLE agent DROP CONSTRAINT IF EXISTS agent_status_check")
    op.execute("ALTER TABLE agent ADD CONSTRAINT agent_status_check CHECK (status IN ('inactive', 'active', 'busy', 'error', 'maintenance'))")

    # Downgrade check constraint to agent.type
    op.execute("ALTER TABLE agent DROP CONSTRAINT IF EXISTS agent_type_check")
    op.execute("ALTER TABLE agent ADD CONSTRAINT agent_type_check CHECK (type IN ('coordinator', 'assistant', 'researcher', 'developer', 'designer', 'specialist', 'auditor', 'custom'))")

    # Downgrade check constraint to task.status
    op.execute("ALTER TABLE task DROP CONSTRAINT IF EXISTS task_status_check")
    op.execute("ALTER TABLE task ADD CONSTRAINT task_status_check CHECK (status IN ('pending', 'assigned', 'in_progress', 'blocked', 'completed', 'failed', 'cancelled'))")

    # Downgrade check constraint to task.priority with integer values (1=LOW, 2=MEDIUM, 3=HIGH, 4=CRITICAL)
    op.execute("ALTER TABLE task DROP CONSTRAINT IF EXISTS task_priority_check")
    op.execute("ALTER TABLE task ADD CONSTRAINT task_priority_check CHECK (priority IN (1, 2, 3, 4))")

    # Downgrade check constraint to tool.integration_type
    op.execute("ALTER TABLE tool DROP CONSTRAINT IF EXISTS tool_integration_type_check")
    op.execute("ALTER TABLE tool ADD CONSTRAINT tool_integration_type_check CHECK (integration_type IN ('api', 'cli', 'library', 'service', 'custom'))")

    # Downgrade check constraint to tool.status
    op.execute("ALTER TABLE tool DROP CONSTRAINT IF EXISTS tool_status_check")
    op.execute("ALTER TABLE tool ADD CONSTRAINT tool_status_check CHECK (status IN ('active', 'inactive', 'deprecated', 'experimental'))")
