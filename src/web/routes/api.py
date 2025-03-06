# src/web/routes/api.py
from flask import Blueprint, jsonify, Response

# Create blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

def create_success_response(data=None, message=None):
    """Create a standardized success response."""
    response
