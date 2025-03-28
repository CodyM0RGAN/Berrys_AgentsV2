"""Add communication metrics tables

Revision ID: 20250327_add_communication_metrics_tables
Revises: 20250326_migrate_to_shared_components
Create Date: 2025-03-27

This migration adds the following tables for the Agent Communication Hub Monitoring and Analytics feature:
1. message_metrics - Stores metrics for individual messages
2. agent_metrics - Stores aggregated metrics for agents
3. topic_metrics - Stores metrics for topics
4. alert_configuration - Stores alert configurations
5. alert_history - Stores alert history
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '20250327_add_communication_metrics_tables'
down_revision = '20250326_migrate_to_shared_components'
branch_labels = None
depends_on = None


def upgrade():
    # Create message_status enum
    op.execute("""
    CREATE TYPE message_status AS ENUM (
        'CREATED', 'ROUTED', 'DELIVERED', 'PROCESSED', 'FAILED'
    )
    """)
    
    # Create metric_type enum
    op.execute("""
    CREATE TYPE metric_type AS ENUM (
        'QUEUE_LENGTH', 'PROCESSING_TIME', 'ROUTING_TIME', 'DELIVERY_TIME', 
        'MESSAGE_COUNT', 'ERROR_RATE', 'TOPIC_ACTIVITY', 'AGENT_ACTIVITY'
    )
    """)
    
    # Create comparison_operator enum
    op.execute("""
    CREATE TYPE comparison_operator AS ENUM (
        'GT', 'LT', 'GTE', 'LTE', 'EQ', 'NEQ'
    )
    """)
    
    # Create alert_severity enum
    op.execute("""
    CREATE TYPE alert_severity AS ENUM (
        'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    )
    """)
    
    # Create message_metrics table
    op.create_table(
        'message_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('correlation_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('source_agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agent.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('destination_agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agent.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('topic', sa.String(), nullable=True, index=True),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('routed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('queue_time_ms', sa.Integer(), nullable=True),
        sa.Column('total_time_ms', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('CREATED', 'ROUTED', 'DELIVERED', 'PROCESSED', 'FAILED', name='message_status'), nullable=False, index=True),
        sa.Column('routing_path', sa.JSON(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True)
    )
    
    # Create agent_metrics table
    op.create_table(
        'agent_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agent.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('messages_sent', sa.Integer(), nullable=False, default=0),
        sa.Column('messages_received', sa.Integer(), nullable=False, default=0),
        sa.Column('average_processing_time_ms', sa.Float(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True)
    )
    
    # Create topic_metrics table
    op.create_table(
        'topic_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('topic', sa.String(), nullable=False, index=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('message_count', sa.Integer(), nullable=False, default=0),
        sa.Column('subscriber_count', sa.Integer(), nullable=False, default=0),
        sa.Column('metadata', sa.JSON(), nullable=True)
    )
    
    # Create alert_configuration table
    op.create_table(
        'alert_configuration',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('metric_type', sa.Enum('QUEUE_LENGTH', 'PROCESSING_TIME', 'ROUTING_TIME', 'DELIVERY_TIME', 
                                         'MESSAGE_COUNT', 'ERROR_RATE', 'TOPIC_ACTIVITY', 'AGENT_ACTIVITY', 
                                         name='metric_type'), nullable=False),
        sa.Column('threshold', sa.Float(), nullable=False),
        sa.Column('comparison', sa.Enum('GT', 'LT', 'GTE', 'LTE', 'EQ', 'NEQ', name='comparison_operator'), nullable=False),
        sa.Column('severity', sa.Enum('INFO', 'WARNING', 'ERROR', 'CRITICAL', name='alert_severity'), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('notification_channels', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True)
    )
    
    # Create alert_history table
    op.create_table(
        'alert_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('alert_configuration_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('alert_configuration.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('message', sa.String(), nullable=False),
        sa.Column('acknowledged', sa.Boolean(), nullable=False, default=False),
        sa.Column('acknowledged_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True)
    )


def downgrade():
    # Drop tables in reverse order
    op.drop_table('alert_history')
    op.drop_table('alert_configuration')
    op.drop_table('topic_metrics')
    op.drop_table('agent_metrics')
    op.drop_table('message_metrics')
    
    # Drop enums
    op.execute('DROP TYPE alert_severity')
    op.execute('DROP TYPE comparison_operator')
    op.execute('DROP TYPE metric_type')
    op.execute('DROP TYPE message_status')
