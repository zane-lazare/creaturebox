# src/web/middleware.py
"""Middleware for the CreatureBox web application."""
from flask import request, g
import time
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Simple rate limiter middleware."""
    
    def __init__(self, app=None, limit=60, window=60):
        """Initialize the rate limiter.
        
        Args:
            app: The Flask app
            limit: Maximum number of requests allowed per window
            window: Time window in seconds
        """
        self.limit = limit
        self.window = window
        self.requests = {}
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the rate limiter with a Flask app."""
        app.before_request(self.before_request)
    
    def before_request(self):
        """Check rate limit before processing request."""
        if not getattr(g, 'rate_limit_enabled', False):
            return
            
        # Get client IP
        client_ip = request.remote_addr
        
        # Get current time
        current_time = time.time()
        
        # Initialize client record if not exists
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        # Clean up old requests
        self.requests[client_ip] = [t for t in self.requests[client_ip] 
                                  if current_time - t < self.window]
        
        # Check if limit exceeded
        if len(self.requests[client_ip]) >= self.limit:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return {
                'status': 'error',
                'error': {
                    'code': 429,
                    'message': 'Rate limit exceeded'
                }
            }, 429
        
        # Add current request
        self.requests[client_ip].append(current_time)

class RequestLogger:
    """Middleware to log API requests."""
    
    def __init__(self, app=None):
        """Initialize the request logger.
        
        Args:
            app: The Flask app
        """
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the request logger with a Flask app."""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        """Log request details before processing."""
        g.start_time = time.time()
    
    def after_request(self, response):
        """Log response details after processing."""
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            logger.info(
                f"{request.remote_addr} - {request.method} {request.path} "
                f"- {response.status_code} - {duration:.4f}s"
            )
        return response
