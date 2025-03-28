"""
Migration script to add the tool_metadata column to the tool table.

This script adds the tool_metadata column to the tool table, which is missing
in the database but exists in the code model.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '03_add_tool_metadata_column'
down_revision = '02_standardize_table_names'
branch_labels = None
depends_on = None


def upgrade():
    """Add tool_metadata column to tool table."""
    # Add tool_metadata column to tool table
    op.add_column('tool', sa.Column('tool_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    
    # Update existing rows to have an empty JSON object as tool_metadata
    op.execute("UPDATE tool SET tool_metadata = '{}'::jsonb WHERE tool_metadata IS NULL")


def downgrade():
    """Remove tool_metadata column from tool table."""
    # Remove tool_metadata column from tool table
    op.drop_column('tool', 'tool_metadata')
