"""
Migration script for Service Integration service to use shared components.

This migration script documents the code changes made to migrate the Service Integration
service to use the shared components developed during the Code Centralization milestone.
No schema changes are needed, as this is purely a code change.

Revision ID: 20250326_migrate_to_shared_components
Revises: service_integration_standardization
Create Date: 2025-03-26 19:18:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '20250326_migrate_to_shared_components'
down_revision = 'service_integration_standardization'
branch_labels = None
depends_on = None


def upgrade():
    """
    Document the code changes made to migrate to shared components.
    
    No schema changes are needed, as this is purely a code change.
    
    Code changes:
    1. Updated internal models to use StandardModel from shared.models.src.base
    2. Updated enum columns to use enum_column() from shared.models.src.base
    3. Updated API models to use shared base classes and utilities
    4. Added configuration management using shared utilities
    """
    # No schema changes needed
    pass


def downgrade():
    """
    Document the code changes needed to revert to the previous implementation.
    
    No schema changes are needed, as this is purely a code change.
    
    Code changes:
    1. Revert internal models to use Base, EnumColumnMixin
    2. Revert enum columns to use direct string columns
    3. Revert API models to use custom base classes
    4. Remove configuration management
    """
    # No schema changes needed
    pass
