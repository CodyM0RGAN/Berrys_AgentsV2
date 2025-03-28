"""add_project_state_table

Revision ID: 9fdeb4ad4a17
Revises: 05_add_berry_agent_configuration
Create Date: 2025-03-26 11:51:33.043274

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9fdeb4ad4a17'
down_revision = '05_add_berry_agent_configuration'
branch_labels = None
depends_on = None


def upgrade():
    # Create project_state table
    op.create_table(
        'project_state',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('state', sa.String(length=20), nullable=False),
        sa.Column('transitioned_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('transitioned_by', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # Drop project_state table
    op.drop_table('project_state')
