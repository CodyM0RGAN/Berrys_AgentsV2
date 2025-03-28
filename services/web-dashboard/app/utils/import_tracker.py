"""
Import tracker utility for the web dashboard application.

This module provides a utility to track imports, especially those related to asyncpg.
"""

import sys
import logging
import traceback

logger = logging.getLogger(__name__)

# Store the original __import__ function
original_import = __import__

def custom_import_hook(name, *args, **kwargs):
    """
    Custom import hook to track imports.
    
    Args:
        name: Name of the module to import
        *args: Additional arguments
        **kwargs: Additional keyword arguments
        
    Returns:
        The imported module
    """
    # Track imports related to database, SQLAlchemy, or asyncpg
    if any(keyword in name.lower() for keyword in ['database', 'sqlalchemy', 'asyncpg', 'postgresql']):
        logger.warning("Importing module: %s", name)
        
        # Log stack trace for asyncpg imports
        if 'asyncpg' in name.lower():
            logger.error("asyncpg import detected!")
            logger.error("Import stack trace: %s", ''.join(traceback.format_stack()))
    
    # Call the original import function
    return original_import(name, *args, **kwargs)

# Install the import hook
sys.modules['builtins'].__import__ = custom_import_hook

logger.info("Import tracker installed")
