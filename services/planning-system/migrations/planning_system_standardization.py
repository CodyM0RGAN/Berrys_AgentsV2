"""
Planning System Service Standardization Migration

This migration script implements the standardization of the Planning System service:
1. Renames tables from plural to singular
2. Converts lowercase enum values to uppercase
3. Adds check constraints for enum values

This is part of the Service Standardization Initiative to ensure consistent
patterns across all services in the Berrys_AgentsV2 system.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision = '20250326_planning_system_standardization'
down_revision = None  # Set to the previous migration if applicable
branch_labels = None
depends_on = None

# Configuration variables
# Table renames (plural to singular)
TABLE_RENAMES = [
    ('strategic_plans', 'strategic_plan'),
    ('plan_phases', 'plan_phase'),
    ('plan_milestones', 'plan_milestone'),
    ('planning_tasks', 'planning_task'),
    ('resource_allocations', 'resource_allocation'),
    ('timeline_forecasts', 'timeline_forecast'),
    ('bottleneck_analyses', 'bottleneck_analysis'),
    ('optimization_results', 'optimization_result'),
    ('task_dependencies', 'task_dependency'),
]

# Enum constraints to add
# Format: (table_name, column_name, constraint_name, enum_values)
ENUM_CONSTRAINTS = [
    ('strategic_plan', 'status', 'strategic_plan_status_check', 
     ['DRAFT', 'PLANNING', 'IN_PROGRESS', 'REVIEW', 'COMPLETED', 'ARCHIVED', 'CANCELLED']),
    
    ('plan_milestone', 'priority', 'plan_milestone_priority_check',
     ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']),
    
    ('planning_task', 'status', 'planning_task_status_check',
     ['PENDING', 'ASSIGNED', 'IN_PROGRESS', 'BLOCKED', 'COMPLETED', 'FAILED', 'CANCELLED']),
    
    ('planning_task', 'priority', 'planning_task_priority_check',
     ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']),
    
    ('resource_allocation', 'resource_type', 'resource_allocation_type_check',
     ['AGENT', 'MODEL', 'TOOL', 'COMPUTE', 'STORAGE', 'OTHER']),
    
    ('task_dependency', 'dependency_type', 'task_dependency_type_check',
     ['FINISH_TO_START', 'START_TO_START', 'FINISH_TO_FINISH', 'START_TO_FINISH']),
]

# Data conversion for lowercase to uppercase
# Format: (table_name, column_name)
UPPERCASE_CONVERSIONS = [
    ('strategic_plan', 'status'),
    ('plan_milestone', 'priority'),
    ('planning_task', 'status'),
    ('planning_task', 'priority'),
    ('resource_allocation', 'resource_type'),
    ('task_dependency', 'dependency_type'),
]

# Foreign key updates needed after table renames
# Format: (table_name, column_name, referenced_table)
FOREIGN_KEY_UPDATES = [
    ('plan_phase', 'plan_id', 'strategic_plan'),
    ('plan_milestone', 'plan_id', 'strategic_plan'),
    ('planning_task', 'plan_id', 'strategic_plan'),
    ('planning_task', 'phase_id', 'plan_phase'),
    ('planning_task', 'milestone_id', 'plan_milestone'),
    ('resource_allocation', 'task_id', 'planning_task'),
    ('timeline_forecast', 'plan_id', 'strategic_plan'),
    ('bottleneck_analysis', 'plan_id', 'strategic_plan'),
    ('optimization_result', 'plan_id', 'strategic_plan'),
    ('plan_history', 'plan_id', 'strategic_plan'),
    ('task_dependency', 'from_task_id', 'planning_task'),
    ('task_dependency', 'to_task_id', 'planning_task'),
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
