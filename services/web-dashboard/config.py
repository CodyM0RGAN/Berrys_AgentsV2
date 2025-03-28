"""
Configuration settings for the Berry's Agents Web Dashboard.
"""
import os
import logging
from datetime import timedelta

# Configure logging
logger = logging.getLogger(__name__)

class Config:
    """Base configuration."""
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-for-development-only')
    FLASK_APP = 'run.py'
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = True
    
    # Database settings (PostgreSQL required)
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
    if not SQLALCHEMY_DATABASE_URI or not SQLALCHEMY_DATABASE_URI.startswith('postgresql'):
        raise ValueError("PostgreSQL database is required. Please set SQLALCHEMY_DATABASE_URI environment variable to a valid PostgreSQL connection string.")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API settings
    API_TIMEOUT = 10  # seconds
    
    # API endpoints
    AGENT_ORCHESTRATOR_API_URL = os.environ.get(
        'AGENT_ORCHESTRATOR_API_URL', 
        'http://localhost:8001/api'
    )
    PROJECT_COORDINATOR_API_URL = os.environ.get(
        'PROJECT_COORDINATOR_API_URL', 
        'http://localhost:8002/api'
    )
    MODEL_ORCHESTRATION_API_URL = os.environ.get(
        'MODEL_ORCHESTRATION_API_URL', 
        'http://localhost:8003/api'
    )
    PLANNING_SYSTEM_API_URL = os.environ.get(
        'PLANNING_SYSTEM_API_URL', 
        'http://localhost:8004/api'
    )
    SERVICE_INTEGRATION_API_URL = os.environ.get(
        'SERVICE_INTEGRATION_API_URL', 
        'http://localhost:8005/api'
    )
    TOOL_INTEGRATION_API_URL = os.environ.get(
        'TOOL_INTEGRATION_API_URL', 
        'http://localhost:8006/api'
    )
    
    # Authentication settings
    AUTH_REQUIRED = os.environ.get('AUTH_REQUIRED', 'False').lower() in ('true', '1', 't')
    
    # Pagination settings
    ITEMS_PER_PAGE = 10
    
    # WebSocket settings
    ENABLE_WEBSOCKETS = os.environ.get('ENABLE_WEBSOCKETS', 'False').lower() in ('true', '1', 't')
    
    # Logging settings
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/web-dashboard.log')
    
    # Static files
    STATIC_FOLDER = 'app/static'
    TEMPLATES_FOLDER = 'app/templates'
    
    # Feature flags
    FEATURE_CHAT = True
    FEATURE_PROJECTS = True
    FEATURE_AGENTS = True
    FEATURE_SETTINGS = True

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False
    
    # Enable more detailed error messages
    EXPLAIN_TEMPLATE_LOADING = True
    
    # Development-specific settings
    SQLALCHEMY_ECHO = True

class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = False
    TESTING = True
    
    # Override the PostgreSQL check for testing
    # This allows the Config class validation to be bypassed for testing
    @property
    def SQLALCHEMY_DATABASE_URI(self):
        return os.environ.get('SQLALCHEMY_DATABASE_URI', 'postgresql://postgres:postgres@postgres:5432/mas_framework_test')
    
    # Disable CSRF protection for testing
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    
    # Use a strong secret key in production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Require HTTPS in production
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    
    # Set stricter content security policy
    CONTENT_SECURITY_POLICY = {
        'default-src': "'self'",
        'script-src': "'self' 'unsafe-inline' https://cdn.jsdelivr.net",
        'style-src': "'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com",
        'font-src': "'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com",
        'img-src': "'self' data:",
        'connect-src': "'self'"
    }

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# Log which configuration is being used
flask_config = os.environ.get('FLASK_CONFIG', 'default')
logger.info(f"Using configuration: {flask_config}")
logger.info(f"Configuration class: {config.get(flask_config, config['default']).__name__}")

# Add a function to get the configuration
def get_config():
    flask_config = os.environ.get('FLASK_CONFIG', 'default')
    logger.info(f"Getting configuration for: {flask_config}")
    config_class = config.get(flask_config, config['default'])
    logger.info(f"Using configuration class: {config_class.__name__}")
    return config_class
