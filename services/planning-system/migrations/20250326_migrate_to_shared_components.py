"""
Planning System Migration to Shared Components

This migration script documents the code changes made to migrate the Planning System service
to use the shared components developed during the Code Centralization milestone.

No schema changes are needed, as this is purely a code change.
"""

from datetime import datetime

# Migration metadata
__migration__ = {
    "name": "Migrate Planning System to Shared Components",
    "version": "20250326",
    "description": "Migrate Planning System service to use shared components",
    "author": "Claude",
    "date": datetime(2025, 3, 26)
}

# Summary of changes
"""
The following changes were made to migrate the Planning System service to use shared components:

1. Updated internal models to use StandardModel from shared.models.src.base
   - Replaced custom base class with StandardModel
   - Removed redundant timestamp fields (created_at, updated_at)
   - Updated UUID handling to use generate_uuid from shared.utils.src.database
   - Changed from direct string columns to using enum_column() from shared.models.src.base

2. Updated API models to use shared base classes and utilities
   - Replaced custom BaseResponseModel with StandardEntityModel
   - Updated pagination models to use shared pagination utilities
   - Updated response models to use shared response templates
   - Added standardized error response models

3. Updated configuration management
   - Replaced custom Settings class with PlanningSystemConfig extending BaseServiceConfig
   - Updated configuration loading to use shared utilities
   - Added service-specific configuration settings

No database schema changes were needed, as the Planning System service was already standardized
in terms of table naming, enum handling, and validation.
"""

# No database operations needed for this migration
def upgrade():
    """No database operations needed for this migration."""
    pass

def downgrade():
    """No database operations needed for this migration."""
    pass
