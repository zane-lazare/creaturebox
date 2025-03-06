# src/web/routes/logs.py
from flask import Blueprint, jsonify, request, send_file, current_app
import io
from ..utils.files import get_log_content
from .api import create_success_response

# Create blueprint
logs_bp = Blueprint('logs', __name__, url_prefix='/api/logs')

@logs_bp.route('/<log_type>')
def logs(log_type):
    """Get log content."""
    content = get_log_content(log_type)
    return jsonify({'content': content})

@logs_bp.route('/<log_type>/download')
def download_log(log_type):
    """Download log file."""
    content = get_log_content(log_type)
    
    # Create in-memory file
    buffer = io.BytesIO()
    buffer.write(content.encode('utf-8'))
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'creaturebox_{log_type}_log.txt',
        mimetype='text/plain'
    )
