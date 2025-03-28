"""
Add alert configuration and alert history tables.

Revision ID: 20250327_add_alert_tables
Revises: 20250327_add_communication_metrics_tables
Create Date: 2025-03-27 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '20250327_add_alert_tables'
down_revision = '20250327_add_communication_metrics_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types
    metric_type = postgresql.ENUM(
        'QUEUE_LENGTH',
        'PROCESSING_TIME',
        'ROUTING_TIME',
        'DELIVERY_TIME',
        'MESSAGE_COUNT',
        'ERROR_RATE',
        'TOPIC_ACTIVITY',
        'AGENT_ACTIVITY',
        name='metric_type'
    )
    metric_type.create(op.get_bind())

    comparison_operator = postgresql.ENUM(
        'GT',
        'LT',
        'GTE',
        'LTE',
        'EQ',
        'NEQ',
        name='comparison_operator'
    )
    comparison_operator.create(op.get_bind())

    alert_severity = postgresql.ENUM(
        'INFO',
        'WARNING',
        'ERROR',
        'CRITICAL',
        name='alert_severity'
    )
    alert_severity.create(op.get_bind())

    # Create alert_configurations table
    op.create_table(
        'alert_configurations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('metric_type', sa.Enum('QUEUE_LENGTH', 'PROCESSING_TIME', 'ROUTING_TIME', 'DELIVERY_TIME', 'MESSAGE_COUNT', 'ERROR_RATE', 'TOPIC_ACTIVITY', 'AGENT_ACTIVITY', name='metric_type'), nullable=False),
        sa.Column('threshold', sa.Float, nullable=False),
        sa.Column('comparison', sa.Enum('GT', 'LT', 'GTE', 'LTE', 'EQ', 'NEQ', name='comparison_operator'), nullable=False),
        sa.Column('severity', sa.Enum('INFO', 'WARNING', 'ERROR', 'CRITICAL', name='alert_severity'), nullable=False),
        sa.Column('enabled', sa.Boolean, nullable=False, default=True),
        sa.Column('notification_channels', postgresql.JSONB, nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    )

    # Create alert_history table
    op.create_table(
        'alert_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('alert_configuration_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('timestamp', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('value', sa.Float, nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('acknowledged', sa.Boolean, nullable=False, default=False),
        sa.Column('acknowledged_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime, nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
        sa.ForeignKeyConstraint(['alert_configuration_id'], ['alert_configurations.id'], ondelete='CASCADE'),
    )

    # Create indexes
    op.create_index('ix_alert_configurations_name', 'alert_configurations', ['name'])
    op.create_index('ix_alert_configurations_metric_type', 'alert_configurations', ['metric_type'])
    op.create_index('ix_alert_configurations_severity', 'alert_configurations', ['severity'])
    op.create_index('ix_alert_configurations_enabled', 'alert_configurations', ['enabled'])
    op.create_index('ix_alert_history_alert_configuration_id', 'alert_history', ['alert_configuration_id'])
    op.create_index('ix_alert_history_timestamp', 'alert_history', ['timestamp'])
    op.create_index('ix_alert_history_acknowledged', 'alert_history', ['acknowledged'])


def downgrade():
    # Drop tables
    op.drop_table('alert_history')
    op.drop_table('alert_configurations')

    # Drop enum types
    op.execute('DROP TYPE alert_severity')
    op.execute('DROP TYPE comparison_operator')
    op.execute('DROP TYPE metric_type')
