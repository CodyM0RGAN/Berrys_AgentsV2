"""
Migration script to standardize table names to singular form.

This script renames the following tables:
- models -> model
- agent_tools -> agent_tool
- task_dependencies -> task_dependency
- provider_quotas -> provider_quota
- requests -> request
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
    """Rename plural tables to singular form."""
    # Rename models to model
    op.rename_table('models', 'model')
    
    # Rename agent_tools to agent_tool
    # Note: This table already has a singular name in the code but plural in the database
    # We're standardizing on the singular form that's used in the code
    op.execute('ALTER TABLE IF EXISTS agent_tools RENAME TO agent_tool')
    
    # Rename task_dependencies to task_dependency
    op.execute('ALTER TABLE IF EXISTS task_dependencies RENAME TO task_dependency')
    
    # Rename provider_quotas to provider_quota
    op.execute('ALTER TABLE IF EXISTS provider_quotas RENAME TO provider_quota')
    
    # Rename requests to request
    op.execute('ALTER TABLE IF EXISTS requests RENAME TO request')
    
    # Update foreign key constraints
    # For agent_tool
    op.execute('ALTER INDEX IF EXISTS agent_tools_pkey RENAME TO agent_tool_pkey')
    op.execute('ALTER TABLE IF EXISTS agent_tool RENAME CONSTRAINT agent_tools_agent_id_fkey TO agent_tool_agent_id_fkey')
    op.execute('ALTER TABLE IF EXISTS agent_tool RENAME CONSTRAINT agent_tools_tool_id_fkey TO agent_tool_tool_id_fkey')
    
    # For task_dependency
    op.execute('ALTER INDEX IF EXISTS task_dependencies_pkey RENAME TO task_dependency_pkey')
    op.execute('ALTER TABLE IF EXISTS task_dependency RENAME CONSTRAINT task_dependencies_dependent_task_id_fkey TO task_dependency_dependent_task_id_fkey')
    op.execute('ALTER TABLE IF EXISTS task_dependency RENAME CONSTRAINT task_dependencies_dependency_task_id_fkey TO task_dependency_dependency_task_id_fkey')


def downgrade():
    """Revert singular tables back to plural form."""
    # Rename model back to models
    op.rename_table('model', 'models')
    
    # Rename agent_tool back to agent_tools
    op.execute('ALTER TABLE IF EXISTS agent_tool RENAME TO agent_tools')
    
    # Rename task_dependency back to task_dependencies
    op.execute('ALTER TABLE IF EXISTS task_dependency RENAME TO task_dependencies')
    
    # Rename provider_quota back to provider_quotas
    op.execute('ALTER TABLE IF EXISTS provider_quota RENAME TO provider_quotas')
    
    # Rename request back to requests
    op.execute('ALTER TABLE IF EXISTS request RENAME TO requests')
    
    # Update foreign key constraints
    # For agent_tools
    op.execute('ALTER INDEX IF EXISTS agent_tool_pkey RENAME TO agent_tools_pkey')
    op.execute('ALTER TABLE IF EXISTS agent_tools RENAME CONSTRAINT agent_tool_agent_id_fkey TO agent_tools_agent_id_fkey')
    op.execute('ALTER TABLE IF EXISTS agent_tools RENAME CONSTRAINT agent_tool_tool_id_fkey TO agent_tools_tool_id_fkey')
    
    # For task_dependencies
    op.execute('ALTER INDEX IF EXISTS task_dependency_pkey RENAME TO task_dependencies_pkey')
    op.execute('ALTER TABLE IF EXISTS task_dependencies RENAME CONSTRAINT task_dependency_dependent_task_id_fkey TO task_dependencies_dependent_task_id_fkey')
    op.execute('ALTER TABLE IF EXISTS task_dependencies RENAME CONSTRAINT task_dependency_dependency_task_id_fkey TO task_dependencies_dependency_task_id_fkey')
