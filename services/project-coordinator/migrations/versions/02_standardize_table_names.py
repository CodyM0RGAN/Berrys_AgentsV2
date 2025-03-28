"""
Migration script to standardize table names to singular form.

This script updates the model definitions to use singular table names.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '02_standardize_table_names'
down_revision = '01_rename_metadata_columns'
branch_labels = None
depends_on = None


def upgrade():
    """
    Update model definitions to use singular table names.
    
    Note: This migration doesn't actually rename any tables because the
    project-coordinator service's tables don't exist in the database yet.
    Instead, we'll update the model definitions to use singular table names.
    """
    # No database changes needed, as the tables don't exist yet.
    # We'll update the model definitions in the code.
    pass


def downgrade():
    """
    Revert model definitions to use plural table names.
    
    Note: This migration doesn't actually rename any tables because the
    project-coordinator service's tables don't exist in the database yet.
    Instead, we'll update the model definitions to use plural table names.
    """
    # No database changes needed, as the tables don't exist yet.
    # We'll update the model definitions in the code.
    pass
