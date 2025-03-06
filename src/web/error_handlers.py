# src/web/error_handlers.py
import logging
from flask import jsonify

logger = logging.getLogger(__name__)

# Error Codes
class ErrorCode:
    # General Errors (1000-1999)
    UNKNOWN_ERROR = 1000
    INVALID_REQUEST = 1001
    RESOURCE_NOT_FOUND = 1002
    
    # File System Errors (2000-2999)
    FILE_NOT_FOUND = 2000
    PERMISSION_DENIED = 2001
    DISK_FULL = 2002
    
    # Camera Errors (3000-3999)
    CAMERA_NOT_FOUND = 3000
    CAMERA_BUSY = 3001
    CAMERA_ERROR = 3002
    
    # System Errors (4000-4999)
    SYSTEM_COMMAND_FAILED = 4000
    SERVICE_UNAVAILABLE = 4001

# Map error codes to HTTP status codes
ERROR_TO_HTTP_STATUS = {
    # General Errors
    ErrorCode.UNKNOWN_ERROR: 500,
    ErrorCode.INVALID_REQUEST: 400,
    ErrorCode.RESOURCE_NOT_FOUND: 404,
    
    # File System Errors
    ErrorCode.FILE_NOT_FOUND: 404,
    ErrorCode.PERMISSION_DENIED: 403,
    ErrorCode.DISK_FULL: 507,
    
    # Camera Errors
    ErrorCode.CAMERA_NOT_FOUND: 404,
    ErrorCode.CAMERA_BUSY: 409,
    ErrorCode.CAMERA_ERROR: 500,
    
    # System Errors
    ErrorCode.SYSTEM_COMMAND_FAILED: 500,
    ErrorCode.SERVICE_UNAVAILABLE: 503,
}

class APIError(Exception):
    """Base exception for API errors."""
    def __init__(self, error_code, message, details=None):
        self.error_code = error_code
        self.message = message
        self.details = details
        super().__init__(self.message)

def create_error_response(error_code, message, details=None):
    """Create a standardized error response."""
    response = {
        'status': 'error',
        'error': {
            'code': error_code,
            'message': message
        }
    }
    
    if details:
        response['error']['details'] = details
        
    return response

def register_error_handlers(app):
    """Register error handlers with the Flask app."""
    
    @app.errorhandler(APIError)
    def handle_api_error(error):
        """Handle custom APIError exceptions."""
        status_code = ERROR_TO_HTTP_STATUS.get(error.error_code, 500)
        
        # Log the error
        logger.error(f"API Error {error.error_code}: {error.message}", 
                    extra={"details": error.details})
        
        response = create_error_response(error.error_code, error.message, error.details)
        return jsonify(response), status_code
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 errors."""
        logger.info(f"Not Found: {error}")
        response = create_error_response(ErrorCode.RESOURCE_NOT_FOUND, "Resource not found")
        return jsonify(response), 404
    
    @app.errorhandler(500)
    def handle_server_error(error):
        """Handle 500 errors."""
        logger.error(f"Server Error: {error}")
        response = create_error_response(ErrorCode.UNKNOWN_ERROR, "Internal server error")
        return jsonify(response), 500
    
    @app.errorhandler(Exception)
    def handle_unhandled_exception(error):
        """Handle unhandled exceptions."""
        logger.exception(f"Unhandled Exception: {error}")
        response = create_error_response(ErrorCode.UNKNOWN_ERROR, "An unexpected error occurred")
        return jsonify(response), 500
