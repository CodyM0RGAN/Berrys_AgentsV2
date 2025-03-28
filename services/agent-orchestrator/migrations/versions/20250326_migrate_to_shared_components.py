"""
Migration script for Agent Orchestrator service.

This migration documents the migration to shared components.
No schema changes are needed, as this is purely a code change.

Revision ID: 20250326_migrate_to_shared_components
Revises: 20250326_create_agent_tables
Create Date: 2025-03-26 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250326_migrate_to_shared_components'
down_revision = '20250326_create_agent_tables'
branch_labels = None
depends_on = None


def upgrade():
    """
    Upgrade to the migration.
    
    This migration documents the following code changes:
    1. Updated internal models to use StandardModel from shared.models.src.base
    2. Updated enum columns to use enum_column() from shared.models.src.base
    3. Updated API models to use shared base classes and utilities
    4. Added configuration management using shared utilities
    
    No schema changes are needed, as this is purely a code change.
    """
    pass


def downgrade():
    """
    Downgrade from the migration.
    
    No schema changes are needed, as this is purely a code change.
    """
    pass
