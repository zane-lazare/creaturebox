# src/web/routes/api.py
from flask import Blueprint, jsonify, Response

# Create blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

def create_success_response(data=None, message=None):
    """Create a standardized success response."""
    response = {'status': 'success'}
    
    if data:
        response['data'] = data
    
    if message:
        response['message'] = message
    
    return response

@api_bp.route('/health')
def health_check():
    """API health check endpoint."""
    return jsonify(create_success_response(
        data={'status': 'healthy'},
        message='API is operational'
    ))
