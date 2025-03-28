import os
import logging
from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO

# Configure logging
logger = logging.getLogger(__name__)

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()
socketio = SocketIO()

def create_app(config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    if config is None:
        # Load the default configuration
        app.config.from_object('config.Config')
    else:
        # Load the specified configuration
        app.config.from_object(config)
    
    # Ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Initialize extensions with the app
    logger.info("Initializing Flask-SQLAlchemy with URI: %s", app.config.get('SQLALCHEMY_DATABASE_URI', 'Not Set')) # Use .get for safety
    if app.config.get('SQLALCHEMY_DATABASE_URI'):
        logger.info("Database driver being used: %s", app.config['SQLALCHEMY_DATABASE_URI'].split('://')[0])
    
    try:
        db.init_app(app)
        logger.info("Flask-SQLAlchemy initialized successfully")
    except Exception as e:
        logger.error("Error initializing Flask-SQLAlchemy: %s", str(e), exc_info=True)
        raise
        
    migrate.init_app(app, db)
    csrf.init_app(app) # Initialize CSRF globally first
    login_manager.init_app(app)
    
    # Configure login manager
    # login_manager.login_view = 'login' # Keep commented out as auth is bypassed
    # login_manager.login_message_category = 'info'
    
    # Initialize SocketIO with the app if enabled
    if app.config.get('ENABLE_WEBSOCKETS', False):
        socketio.init_app(app, cors_allowed_origins="*")
    
    # Initialize API clients
    from app.api.clients import init_api_clients, close_api_clients
    init_api_clients(app)
    app.teardown_appcontext(close_api_clients) # Ensure clients are closed
    
    # Register routes
    with app.app_context():
        # Import route modules and blueprints
        from app.routes import main, auth, projects, chat, settings, metrics, plans # Keep non-API routes
        from app.routes.api import api_blueprint # Import the new API blueprint
        from app.routes.errors import register_error_handlers # Import error handlers
        
        # Register non-API routes directly (if not using blueprints for them)
        main.register_routes(app)
        projects.register_routes(app)
        plans.register_routes(app)
        chat.register_routes(app) # This will now only register /chat
        settings.register_routes(app)
        metrics.register_routes(app) # Register metrics routes
        # auth.register_routes(app) # Keep auth commented out

        # Register the API blueprint
        app.register_blueprint(api_blueprint)
        
        # Exempt the API blueprint from CSRF protection
        csrf.exempt(api_blueprint)
        logger.info("Exempted API blueprint from CSRF protection.")
        
        # Register error handlers
        register_error_handlers(app)
        
        # Create database tables if they don't exist
        logger.info("Creating database tables if they don't exist")
        try:
            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error("Error creating database tables: %s", str(e), exc_info=True)
            raise
    
    return app
