"""
Enum Standardization Migration Template

This template provides a starting point for creating Alembic migrations to standardize
enum values in a service's database. It includes:

1. Table renaming (plural to singular)
2. Adding check constraints for enum values
3. Converting existing data from lowercase to uppercase

Usage:
1. Copy this template to your service's migrations/versions directory
2. Rename it with a timestamp and descriptive name (e.g., 20250405_123456_standardize_enums.py)
3. Customize the variables and SQL statements for your specific service
4. Run the migration using Alembic

Note: Always test migrations in a development environment before applying to production.
"""

# Standard imports for Alembic migrations
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
# Change these when creating a real migration
revision = 'template_revision_id'
down_revision = 'previous_revision_id'
branch_labels = None
depends_on = None

# Configuration variables - customize these for your service
# Table renames (plural to singular)
TABLE_RENAMES = [
    ('agents', 'agent'),
    ('agent_templates', 'agent_template'),
    ('agent_executions', 'agent_execution'),
    # Add more tables as needed
]

# Enum constraints to add
# Format: (table_name, column_name, constraint_name, enum_values)
ENUM_CONSTRAINTS = [
    ('agent', 'status', 'agent_status_check', 
     ['CREATED', 'INITIALIZING', 'READY', 'ACTIVE', 'PAUSED', 'ERROR', 'TERMINATED']),
    ('agent', 'type', 'agent_type_check',
     ['COORDINATOR', 'ASSISTANT', 'RESEARCHER', 'DEVELOPER', 'DESIGNER', 'SPECIALIST', 'AUDITOR', 'CUSTOM']),
    # Add more constraints as needed
]

# Data conversion for lowercase to uppercase
# Format: (table_name, column_name)
UPPERCASE_CONVERSIONS = [
    ('agent', 'status'),
    ('agent', 'type'),
    # Add more columns as needed
]


def upgrade():
    """
    Upgrade to standardized enums:
    1. Rename tables from plural to singular
    2. Add check constraints for enum values
    3. Convert existing data from lowercase to uppercase
    """
    # Step 1: Rename tables from plural to singular
    for old_name, new_name in TABLE_RENAMES:
        op.rename_table(old_name, new_name)
        print(f"Renamed table '{old_name}' to '{new_name}'")
    
    # Step 2: Convert data from lowercase to uppercase
    connection = op.get_bind()
    for table_name, column_name in UPPERCASE_CONVERSIONS:
        # Create a temporary function to uppercase values
        connection.execute(f"""
        UPDATE {table_name}
        SET {column_name} = UPPER({column_name})
        WHERE {column_name} != UPPER({column_name})
        """)
        print(f"Converted lowercase values to uppercase in {table_name}.{column_name}")
    
    # Step 3: Add check constraints for enum values
    for table_name, column_name, constraint_name, enum_values in ENUM_CONSTRAINTS:
        # Format the enum values for SQL
        values_str = ', '.join(f"'{value}'" for value in enum_values)
        
        # Add the check constraint
        op.execute(f"""
        ALTER TABLE {table_name}
        ADD CONSTRAINT {constraint_name}
        CHECK ({column_name} IN ({values_str}))
        """)
        print(f"Added check constraint '{constraint_name}' to {table_name}.{column_name}")


def downgrade():
    """
    Downgrade from standardized enums:
    1. Remove check constraints
    2. Convert data from uppercase to lowercase (if needed)
    3. Rename tables from singular to plural
    """
    # Step 1: Remove check constraints
    connection = op.get_bind()
    for table_name, column_name, constraint_name, _ in ENUM_CONSTRAINTS:
        op.drop_constraint(constraint_name, table_name)
        print(f"Dropped check constraint '{constraint_name}' from {table_name}")
    
    # Step 2: Convert data from uppercase to lowercase (if needed)
    # Note: This is optional and depends on your requirements
    # Uncomment if you need to convert back to lowercase
    """
    for table_name, column_name in UPPERCASE_CONVERSIONS:
        connection.execute(f'''
        UPDATE {table_name}
        SET {column_name} = LOWER({column_name})
        ''')
        print(f"Converted uppercase values to lowercase in {table_name}.{column_name}")
    """
    
    # Step 3: Rename tables from singular to plural
    for old_name, new_name in TABLE_RENAMES:
        op.rename_table(new_name, old_name)
        print(f"Renamed table '{new_name}' back to '{old_name}'")
