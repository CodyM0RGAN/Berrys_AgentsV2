"""Migrate to shared components

Revision ID: 20250326_migrate_to_shared_components
Revises: <previous_revision_id>
Create Date: 2025-03-26 19:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250326_migrate_to_shared_components'
down_revision = '<previous_revision_id>'
branch_labels = None
depends_on = None

def upgrade():
    # Update tool table to use StandardModel
    op.add_column('tool', sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
    op.add_column('tool', sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
    op.add_column('tool', sa.Column('version', sa.Integer(), nullable=False, server_default=sa.text('1')))
    
    # Update tool_category table to use StandardModel
    op.add_column('tool_category', sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
    op.add_column('tool_category', sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
    op.add_column('tool_category', sa.Column('version', sa.Integer(), nullable=False, server_default=sa.text('1')))
    
    # Update tool_execution table to use StandardModel
    op.add_column('tool_execution', sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
    op.add_column('tool_execution', sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
    op.add_column('tool_execution', sa.Column('version', sa.Integer(), nullable=False, server_default=sa.text('1')))
    
    # Add triggers for updated_at
    op.execute("""
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = CURRENT_TIMESTAMP;
        NEW.version = OLD.version + 1;
        RETURN NEW;
    END;
    $$ language 'plpgsql';
    """)
    
    op.execute("""
    CREATE TRIGGER update_tool_updated_at
        BEFORE UPDATE ON tool
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)
    
    op.execute("""
    CREATE TRIGGER update_tool_category_updated_at
        BEFORE UPDATE ON tool_category
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)
    
    op.execute("""
    CREATE TRIGGER update_tool_execution_updated_at
        BEFORE UPDATE ON tool_execution
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)

def downgrade():
    # Remove triggers
    op.execute("DROP TRIGGER IF EXISTS update_tool_updated_at ON tool;")
    op.execute("DROP TRIGGER IF EXISTS update_tool_category_updated_at ON tool_category;")
    op.execute("DROP TRIGGER IF EXISTS update_tool_execution_updated_at ON tool_execution;")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")
    
    # Remove StandardModel columns from tool table
    op.drop_column('tool', 'created_at')
    op.drop_column('tool', 'updated_at')
    op.drop_column('tool', 'version')
    
    # Remove StandardModel columns from tool_category table
    op.drop_column('tool_category', 'created_at')
    op.drop_column('tool_category', 'updated_at')
    op.drop_column('tool_category', 'version')
    
    # Remove StandardModel columns from tool_execution table
    op.drop_column('tool_execution', 'created_at')
    op.drop_column('tool_execution', 'updated_at')
    op.drop_column('tool_execution', 'version')
