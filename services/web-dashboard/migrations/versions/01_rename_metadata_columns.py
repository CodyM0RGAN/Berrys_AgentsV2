"""
Migration script to rename 'metadata' columns to avoid SQLAlchemy reserved name conflicts.

This script renames the following columns:
- project.metadata -> project.project_metadata
- tool.metadata -> tool.tool_metadata
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '01_rename_metadata_columns'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Rename metadata columns to avoid SQLAlchemy reserved name conflicts."""
    # Rename project.metadata to project.project_metadata
    op.alter_column('project', 'metadata', new_column_name='project_metadata',
                   existing_type=postgresql.JSON(astext_type=sa.Text()))
    
    # Rename tool.metadata to tool.tool_metadata
    op.alter_column('tool', 'metadata', new_column_name='tool_metadata',
                   existing_type=postgresql.JSON(astext_type=sa.Text()))


def downgrade():
    """Revert column renames (for rollback)."""
    # Rename project.project_metadata back to project.metadata
    op.alter_column('project', 'project_metadata', new_column_name='metadata',
                   existing_type=postgresql.JSON(astext_type=sa.Text()))
    
    # Rename tool.tool_metadata back to tool.metadata
    op.alter_column('tool', 'tool_metadata', new_column_name='metadata',
                   existing_type=postgresql.JSON(astext_type=sa.Text()))
