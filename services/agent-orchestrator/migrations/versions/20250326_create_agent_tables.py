"""Create agent orchestrator tables

Revision ID: 20250326_create_agent_tables
Revises: 
Create Date: 2025-03-26

This migration creates the following tables for the Agent Orchestrator service:
1. agent_template
2. agent_execution
3. agent_checkpoint
4. agent_state_history
5. execution_state_history

Note: The agent table and human_interaction table already exist in the database.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '20250326_create_agent_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create agent_template table
    op.create_table(
        'agent_template',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('agent_type', sa.String(20), nullable=False),
        sa.Column('configuration_schema', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('default_configuration', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('prompt_template', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "agent_type IN ('COORDINATOR', 'ASSISTANT', 'RESEARCHER', 'DEVELOPER', 'DESIGNER', 'SPECIALIST', 'AUDITOR', 'CUSTOM')",
            name='agent_template_agent_type_check'
        )
    )
    
    # Create agent_state_history table
    op.create_table(
        'agent_state_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agent.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('previous_status', sa.String(20), nullable=True),
        sa.Column('new_status', sa.String(20), nullable=False),
        sa.Column('previous_state_detail', sa.String(20), nullable=True),
        sa.Column('new_state_detail', sa.String(20), nullable=True),
        sa.Column('reason', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
        sa.CheckConstraint(
            "previous_status IS NULL OR previous_status IN ('INACTIVE', 'ACTIVE', 'BUSY', 'ERROR', 'MAINTENANCE')",
            name='agent_state_history_previous_status_check'
        ),
        sa.CheckConstraint(
            "new_status IN ('INACTIVE', 'ACTIVE', 'BUSY', 'ERROR', 'MAINTENANCE')",
            name='agent_state_history_new_status_check'
        ),
        sa.CheckConstraint(
            "previous_state_detail IS NULL OR previous_state_detail IN ('CREATED', 'INITIALIZING', 'READY', 'ACTIVE', 'PAUSED', 'ERROR', 'TERMINATED')",
            name='agent_state_history_previous_state_detail_check'
        ),
        sa.CheckConstraint(
            "new_state_detail IS NULL OR new_state_detail IN ('CREATED', 'INITIALIZING', 'READY', 'ACTIVE', 'PAUSED', 'ERROR', 'TERMINATED')",
            name='agent_state_history_new_state_detail_check'
        )
    )
    
    # Create agent_checkpoint table
    op.create_table(
        'agent_checkpoint',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agent.id', ondelete='CASCADE'), nullable=False, index=True, unique=True),
        sa.Column('state_data', sa.JSON(), nullable=False),
        sa.Column('sequence_number', sa.Integer(), nullable=False, default=0),
        sa.Column('is_recoverable', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    
    # Create agent_execution table
    op.create_table(
        'agent_execution',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agent.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('state', sa.String(20), nullable=False, default='QUEUED'),
        sa.Column('parameters', sa.JSON(), nullable=True),
        sa.Column('context', sa.JSON(), nullable=True),
        sa.Column('progress_percentage', sa.Float(), nullable=False, default=0.0),
        sa.Column('status_message', sa.String(), nullable=True),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "state IN ('QUEUED', 'PREPARING', 'RUNNING', 'PAUSED', 'COMPLETED', 'FAILED', 'CANCELLED')",
            name='agent_execution_state_check'
        )
    )
    
    # Create execution_state_history table
    op.create_table(
        'execution_state_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('execution_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agent_execution.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('previous_state', sa.String(20), nullable=True),
        sa.Column('new_state', sa.String(20), nullable=False),
        sa.Column('reason', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
        sa.CheckConstraint(
            "previous_state IS NULL OR previous_state IN ('QUEUED', 'PREPARING', 'RUNNING', 'PAUSED', 'COMPLETED', 'FAILED', 'CANCELLED')",
            name='execution_state_history_previous_state_check'
        ),
        sa.CheckConstraint(
            "new_state IN ('QUEUED', 'PREPARING', 'RUNNING', 'PAUSED', 'COMPLETED', 'FAILED', 'CANCELLED')",
            name='execution_state_history_new_state_check'
        )
    )
    
    # Add state_detail column to agent table if it doesn't exist
    op.add_column('agent', sa.Column('state_detail', sa.String(20), nullable=True))
    op.create_check_constraint(
        'agent_state_detail_check',
        'agent',
        "state_detail IS NULL OR state_detail IN ('CREATED', 'INITIALIZING', 'READY', 'ACTIVE', 'PAUSED', 'ERROR', 'TERMINATED')"
    )


def downgrade():
    # Drop state_detail column from agent table
    op.drop_constraint('agent_state_detail_check', 'agent', type_='check')
    op.drop_column('agent', 'state_detail')
    
    # Drop tables in reverse order
    op.drop_table('execution_state_history')
    op.drop_table('agent_execution')
    op.drop_table('agent_checkpoint')
    op.drop_table('agent_state_history')
    op.drop_table('agent_template')
