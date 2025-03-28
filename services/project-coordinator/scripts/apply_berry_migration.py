#!/usr/bin/env python
"""
Script to apply the Berry agent configuration migration.

This script applies the migrations that:
1. Create the agent-related tables (agent_instruction, agent_capability, agent_knowledge_domain)
2. Create the chat-related tables (chat_session, chat_message)
3. Create the agent_prompt_template table
4. Insert Berry's configuration into the database

Berry is a versatile assistant who engages in friendly conversations while also helping users
create and manage projects. Berry recognizes when conversations might lead to project opportunities
and can guide users through the project creation process.

The script verifies that Berry's configuration exists in the database after the migration.
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

from src.models.internal import Base, AgentInstructions
from src.repositories.agent_repository import AgentRepository


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def get_alembic_config(alembic_ini_path):
    """Get the Alembic configuration."""
    if not os.path.exists(alembic_ini_path):
        raise FileNotFoundError(f"Alembic config file not found: {alembic_ini_path}")
    
    config = Config(alembic_ini_path)
    return config


def run_migration(config):
    """Run the migration to the latest version."""
    logger.info("Running migration to the latest version...")
    command.upgrade(config, "head")
    logger.info("Migration completed successfully.")


def verify_berry_configuration(db_url):
    """Verify that Berry's configuration exists in the database."""
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Check if the agent_prompt_template table exists
        inspector = inspect(engine)
        if "agent_prompt_template" not in inspector.get_table_names():
            logger.error("agent_prompt_template table does not exist. Migration failed.")
            return False
        
        # Check if Berry's configuration exists
        repository = AgentRepository(session)
        berry_config = repository.get_complete_agent_configuration("Berry")
        if not berry_config:
            logger.error("Berry's configuration does not exist. Migration failed.")
            return False
        
        # Check if Berry's prompt templates exist
        if "prompt_templates" not in berry_config or not berry_config["prompt_templates"]:
            logger.error("Berry's prompt templates do not exist. Migration failed.")
            return False
        
        # Check if Berry's capabilities exist
        if "capabilities" not in berry_config or not berry_config["capabilities"]:
            logger.error("Berry's capabilities do not exist. Migration failed.")
            return False
        
        # Check if Berry's knowledge domains exist
        if "knowledge_domains" not in berry_config or not berry_config["knowledge_domains"]:
            logger.error("Berry's knowledge domains do not exist. Migration failed.")
            return False
        
        logger.info("Berry's configuration verified successfully.")
        return True
    
    finally:
        session.close()


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Apply Berry agent configuration migration")
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
        
        # Verify Berry's configuration
        if not verify_berry_configuration(db_url):
            return 1
        
        logger.info("Berry agent configuration migration applied successfully.")
        return 0
    
    except Exception as e:
        logger.error(f"Error applying Berry agent configuration migration: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
