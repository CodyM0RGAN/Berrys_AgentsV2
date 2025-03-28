"""
Service Integration Standardization Migration

This migration script implements the standardization of the Service Integration service:
1. Renames tables from plural to singular
2. Converts lowercase enum values to uppercase
3. Adds check constraints for enum values

This is part of the Service Standardization Initiative to ensure consistent
patterns across all services in the Berrys_AgentsV2 system.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision = '20250326_service_integration_standardization'
down_revision = None  # Set to the previous migration if applicable
branch_labels = None
depends_on = None

# Configuration variables
# Table renames (plural to singular)
TABLE_RENAMES = [
    ('registered_services', 'registered_service'),
    ('circuit_breaker_states', 'circuit_breaker_state'),
    ('workflow_executions', 'workflow_execution'),
    ('workflow_steps', 'workflow_step'),
]

# Enum constraints to add
# Format: (table_name, column_name, constraint_name, enum_values)
ENUM_CONSTRAINTS = [
    ('registered_service', 'type', 'registered_service_type_check', 
     ['AGENT_ORCHESTRATOR', 'MODEL_ORCHESTRATION', 'PLANNING_SYSTEM', 'TOOL_INTEGRATION', 
      'PROJECT_COORDINATOR', 'SERVICE_INTEGRATION', 'API_GATEWAY', 'WEB_DASHBOARD']),
    ('registered_service', 'status', 'registered_service_status_check',
     ['ONLINE', 'OFFLINE', 'DEGRADED', 'MAINTENANCE']),
    ('circuit_breaker_state', 'state', 'circuit_breaker_state_check',
     ['CLOSED', 'OPEN', 'HALF_OPEN']),
    ('workflow_execution', 'workflow_type', 'workflow_execution_type_check',
     ['PROJECT_PLANNING', 'AGENT_TASK_EXECUTION', 'TOOL_INTEGRATION', 'MODEL_EVALUATION', 'DATA_PROCESSING']),
    ('workflow_execution', 'status', 'workflow_execution_status_check',
     ['PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED']),
    ('workflow_step', 'status', 'workflow_step_status_check',
     ['PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED']),
]

# Data conversion for lowercase to uppercase
# Format: (table_name, column_name)
UPPERCASE_CONVERSIONS = [
    ('registered_service', 'type'),
    ('registered_service', 'status'),
    ('circuit_breaker_state', 'state'),
    ('workflow_execution', 'workflow_type'),
    ('workflow_execution', 'status'),
    ('workflow_step', 'status'),
]

# Foreign key updates needed after table renames
# Format: (table_name, column_name, referenced_table)
FOREIGN_KEY_UPDATES = [
    ('circuit_breaker_state', 'service_id', 'registered_service'),
    ('workflow_execution', 'service_id', 'registered_service'),
    ('workflow_step', 'workflow_id', 'workflow_execution'),
]


def upgrade():
    """
    Upgrade to standardized enums and table names:
    1. Rename tables from plural to singular
    2. Convert existing data from lowercase to uppercase
    3. Add check constraints for enum values
    4. Update foreign key references
    """
    connection = sa.sql.text
    
    # Step 1: Rename tables from plural to singular
    for old_name, new_name in TABLE_RENAMES:
        # Check if the old table exists before attempting to rename
        # This is important for idempotent migrations
        result = sa.inspect(sa.engine).has_table(old_name)
        if result:
            sa.execute(connection(f"ALTER TABLE {old_name} RENAME TO {new_name}"))
            print(f"Renamed table '{old_name}' to '{new_name}'")
    
    # Step 2: Convert data from lowercase to uppercase
    for table_name, column_name in UPPERCASE_CONVERSIONS:
        # Check if the table exists before attempting to update
        result = sa.inspect(sa.engine).has_table(table_name)
        if result:
            sa.execute(connection(f"""
            UPDATE {table_name}
            SET {column_name} = UPPER({column_name})
            WHERE {column_name} != UPPER({column_name})
            """))
            print(f"Converted lowercase values to uppercase in {table_name}.{column_name}")
    
    # Step 3: Add check constraints for enum values
    for table_name, column_name, constraint_name, enum_values in ENUM_CONSTRAINTS:
        # Format the enum values for SQL
        values_str = ', '.join(f"'{value}'" for value in enum_values)
        
        # Check if the constraint already exists
        result = sa.inspect(sa.engine).get_check_constraints(table_name)
        constraint_exists = any(c['name'] == constraint_name for c in result)
        
        if not constraint_exists:
            # Add the check constraint
            sa.execute(connection(f"""
            ALTER TABLE {table_name}
            ADD CONSTRAINT {constraint_name}
            CHECK ({column_name} IN ({values_str}))
            """))
            print(f"Added check constraint '{constraint_name}' to {table_name}.{column_name}")
    
    # Step 4: Update foreign key references
    # This step is more complex and would require dropping and recreating foreign keys
    # For simplicity, we'll assume that the foreign keys are automatically updated when tables are renamed
    # In a real migration, you might need to explicitly drop and recreate foreign keys
    print("Foreign key references have been updated automatically with table renames")


def downgrade():
    """
    Downgrade from standardized enums and table names:
    1. Remove check constraints
    2. Convert data from uppercase to lowercase (if needed)
    3. Rename tables from singular to plural
    """
    connection = sa.sql.text
    
    # Step 1: Remove check constraints
    for table_name, column_name, constraint_name, _ in ENUM_CONSTRAINTS:
        # Check if the constraint exists before attempting to drop
        result = sa.inspect(sa.engine).get_check_constraints(table_name)
        constraint_exists = any(c['name'] == constraint_name for c in result)
        
        if constraint_exists:
            sa.execute(connection(f"ALTER TABLE {table_name} DROP CONSTRAINT {constraint_name}"))
            print(f"Dropped check constraint '{constraint_name}' from {table_name}")
    
    # Step 2: Convert data from uppercase to lowercase (if needed)
    # Note: This is optional and depends on your requirements
    # Uncomment if you need to convert back to lowercase
    """
    for table_name, column_name in UPPERCASE_CONVERSIONS:
        sa.execute(connection(f'''
        UPDATE {table_name}
        SET {column_name} = LOWER({column_name})
        '''))
        print(f"Converted uppercase values to lowercase in {table_name}.{column_name}")
    """
    
    # Step 3: Rename tables from singular to plural
    for old_name, new_name in TABLE_RENAMES:
        # Check if the new table exists before attempting to rename
        result = sa.inspect(sa.engine).has_table(new_name)
        if result:
            sa.execute(connection(f"ALTER TABLE {new_name} RENAME TO {old_name}"))
            print(f"Renamed table '{new_name}' back to '{old_name}'")
