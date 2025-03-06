# src/web/routes/scheduler.py
from flask import Blueprint, jsonify, request, current_app
from ..utils.files import read_csv_settings, write_csv_settings
from ..utils.system import run_script
from ..error_handlers import APIError, ErrorCode
from .api import create_success_response
from ..config import SCHEDULE_SETTINGS_FILE

# Create blueprint
scheduler_bp = Blueprint('scheduler', __name__, url_prefix='/api/schedule')

@scheduler_bp.route('/settings', methods=['GET'])
def get_schedule_settings():
    """Get schedule settings."""
    settings = read_csv_settings(SCHEDULE_SETTINGS_FILE)
    return jsonify(settings)

@scheduler_bp.route('/settings', methods=['POST'])
def update_schedule_settings():
    """Update schedule settings."""
    settings = request.get_json()
    success = write_csv_settings(SCHEDULE_SETTINGS_FILE, settings)
    
    # Also update runtime in control file if present
    if 'runtime' in settings:
        from ..utils.system import write_control_values
        write_control_values({'runtime': settings['runtime']})
    
    if success:
        # Run scheduler script to apply new settings
        try:
            run_script('Scheduler.py')
            return jsonify(create_success_response(message='Schedule settings updated'))
        except Exception as e:
            current_app.logger.error(f"Error running scheduler script: {str(e)}")
            raise APIError(
                ErrorCode.SYSTEM_COMMAND_FAILED,
                "Failed to apply schedule settings",
                {"error": str(e)}
            )
    else:
        raise APIError(
            ErrorCode.UNKNOWN_ERROR,
            "Failed to update schedule settings"
        )
