"""
Migration script for Model Orchestration service to use shared components.

Revision ID: 20250326_migrate_to_shared_components
Revises: (previous revision ID)
Create Date: 2025-03-26

This migration documents the code changes made to migrate the Model Orchestration
service to use the shared components developed during the Code Centralization milestone.
No schema changes are needed, as this is purely a code change.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = '20250326_migrate_to_shared_components'
down_revision = None  # Update with the previous migration ID when available
branch_labels = None
depends_on = None


def upgrade():
    """
    Document the code changes made to migrate to shared components.
    
    Code changes:
    1. Updated internal models to use StandardModel from shared.models.src.base
    2. Updated enum columns to use enum_column() from shared.models.src.base
    3. Updated API models to use shared base classes and utilities
    4. Added configuration management using shared utilities
    
    No schema changes are needed, as this is purely a code change.
    """
    pass


def downgrade():
    """
    Document how to revert the code changes.
    
    Code changes to revert:
    1. Revert internal models to use Base, EnumColumnMixin
    2. Revert enum columns to use String columns
    3. Revert API models to use custom base classes
    4. Revert configuration management to use custom implementation
    
    No schema changes are needed, as this is purely a code change.
    """
    pass
