"""
Migration script to rename 'metadata' columns to avoid SQLAlchemy reserved name conflicts.

This migration is a no-op because we create the tables with the correct column names
in the 03_create_agent_tables migration. The original purpose was to rename the following columns:
- chat_session.metadata -> chat_session.session_metadata
- chat_message.metadata -> chat_message.message_metadata

'metadata' is a reserved name in SQLAlchemy, so we need to use different column names
to avoid conflicts with SQLAlchemy's internal metadata.
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
    # This migration is a no-op because we'll create the tables with the correct column names
    # in the 03_create_agent_tables migration
    pass


def downgrade():
    """Revert column renames (for rollback)."""
    # This migration is a no-op because we'll create the tables with the correct column names
    # in the 03_create_agent_tables migration
    pass
