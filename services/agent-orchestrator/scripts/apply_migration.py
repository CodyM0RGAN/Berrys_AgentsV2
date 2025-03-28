#!/usr/bin/env python
"""
Script to apply the Agent Orchestrator service migrations.

This script applies the migrations that:
1. Create the agent_template table
2. Create the agent_execution table
3. Create the agent_checkpoint table
4. Create the agent_state_history table
5. Create the execution_state_history table
6. Add the state_detail column to the agent table

The script verifies that the tables exist in the database after the migration.
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Add the parent directory to the Python path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)

# Add the project root to the Python path for shared modules
project_root = os.path.abspath(os.path.join(parent_dir, '../..'))
sys.path.insert(0, project_root)

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from src.models.internal import Base


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def get_alembic_config(alembic_ini_path):
    """Get the Alembic configuration."""
    # If the path is relative, check if it exists in the parent directory
    if not os.path.isabs(alembic_ini_path) and not os.path.exists(alembic_ini_path):
        parent_dir_path = os.path.join(os.path.dirname(__file__), '..', alembic_ini_path)
        if os.path.exists(parent_dir_path):
            alembic_ini_path = parent_dir_path
    
    if not os.path.exists(alembic_ini_path):
        raise FileNotFoundError(f"Alembic config file not found: {alembic_ini_path}")
    
    config = Config(alembic_ini_path)
    return config


def run_migration(config):
    """Run the migration to the latest version."""
    logger.info("Running migration to the latest version...")
    command.upgrade(config, "head")
    logger.info("Migration completed successfully.")


def verify_tables(db_url):
    """Verify that the tables exist in the database."""
    engine = create_engine(db_url)
    inspector = inspect(engine)
    
    # List of tables that should exist after the migration
    expected_tables = [
        "agent_template",
        "agent_execution",
        "agent_checkpoint",
        "agent_state_history",
        "execution_state_history"
    ]
    
    # Check if all expected tables exist
    existing_tables = inspector.get_table_names()
    for table in expected_tables:
        if table not in existing_tables:
            logger.error(f"Table {table} does not exist. Migration failed.")
            return False
    
    # Check if the agent table has the state_detail column
    if "agent" in existing_tables:
        columns = [column["name"] for column in inspector.get_columns("agent")]
        if "state_detail" not in columns:
            logger.error("state_detail column does not exist in the agent table. Migration failed.")
            return False
    else:
        logger.error("agent table does not exist. Migration failed.")
        return False
    
    logger.info("All tables and columns verified successfully.")
    return True


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Apply Agent Orchestrator service migrations")
    parser.add_argument(
        "--alembic-ini", 
        default="alembic.ini", 
        help="Path to alembic.ini file"
    )
    parser.add_argument(
        "--db-url", 
        help="Database URL (overrides the one in alembic.ini)"
    )
    args = parser.parse_args()
    
    try:
        # Get the Alembic configuration
        config = get_alembic_config(args.alembic_ini)
        
        # Override the database URL if provided
        if args.db_url:
            config.set_main_option("sqlalchemy.url", args.db_url)
        
        # Get the database URL from the config
        db_url = config.get_main_option("sqlalchemy.url")
        if not db_url:
            logger.error("Database URL not found in alembic.ini")
            return 1
        
        # Run the migration
        run_migration(config)
        
        # Verify that the tables exist
        if not verify_tables(db_url):
            return 1
        
        logger.info("Agent Orchestrator service migrations applied successfully.")
        return 0
    
    except Exception as e:
        logger.error(f"Error applying Agent Orchestrator service migrations: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
