#!/usr/bin/env python
"""
Run script for the Berry's Agents Web Dashboard.
"""
# Import the tracker before anything else
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
from app.utils import import_tracker

import os
from app import create_app

# Import the configuration function
from config import get_config

# Create the Flask application with the correct configuration
app = create_app(get_config())

if __name__ == '__main__':
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 5000))
    
    # Get debug mode from environment variable or use default
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() in ('true', '1', 't')
    
    # Run the application
    app.run(
        host='0.0.0.0',  # Make the server publicly available
        port=port,
        debug=debug
    )
