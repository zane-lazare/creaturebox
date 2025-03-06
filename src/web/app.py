# src/web/app.py
import os
import sys
import logging
from flask import Flask, render_template, send_from_directory
from flask_cors import CORS

# Import configuration and utilities
from .config import HOST, PORT, DEBUG, THREADED, LOG_DIR, LOG_FORMAT, LOG_LEVEL, ENABLE_RATE_LIMITING, API_RATE_LIMIT
from .error_handlers import register_error_handlers
from .middleware import RateLimiter, RequestLogger

# Import route blueprints
from .routes.api import api_bp
from .routes.system import system_bp
from .routes.camera import camera_bp
from .routes.gallery import gallery_bp
from .routes.logs import logs_bp
from .routes.scheduler import scheduler_bp
from .routes.network import network_bp

def create_app():
    """Create and configure the Flask application."""
    # Initialize app
    app = Flask(__name__, static_folder='static', static_url_path='')
    
    # Enable CORS
    CORS(app)
    
    # Configure logging
    setup_logging(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Enable middleware
    setup_middleware(app)
    
    # Set up routes
    setup_routes(app)
    
    return app

def setup_logging(app):
    """Configure application logging."""
    # Ensure log directory exists
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # Create file handler
    file_handler = logging.FileHandler(os.path.join(LOG_DIR, 'creaturebox_web.log'))
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    
    # Set logging level
    app.logger.setLevel(getattr(logging, LOG_LEVEL))
    app.logger.addHandler(file_handler)
    
    # Set root logger for imported modules
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, LOG_LEVEL))
    root_logger.addHandler(file_handler)
    
    # Silence Flask's built-in logger
    logging.getLogger('werkzeug').setLevel(logging.WARNING)

def register_blueprints(app):
    """Register all blueprint routes."""
    app.register_blueprint(api_bp)
    app.register_blueprint(system_bp)
    app.register_blueprint(camera_bp)
    app.register_blueprint(gallery_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(scheduler_bp)
    app.register_blueprint(network_bp)

def setup_middleware(app):
    """Configure application middleware."""
    # Request logger
    request_logger = RequestLogger()
    request_logger.init_app(app)
    
    # Rate limiter (optional)
    if ENABLE_RATE_LIMITING:
        rate_limiter = RateLimiter(limit=API_RATE_LIMIT)
        rate_limiter.init_app(app)

def setup_routes(app):
    """Set up basic routes."""
    @app.route('/')
    def index():
        """Serve the main HTML page."""
        return app.send_static_file('index.html')
    
    @app.route('/favicon.ico')
    def favicon():
        """Serve the favicon."""
        return app.send_static_file('img/favicon.ico')

if __name__ == '__main__':
    app = create_app()
    app.run(host=HOST, port=PORT, debug=DEBUG, threaded=THREADED)
