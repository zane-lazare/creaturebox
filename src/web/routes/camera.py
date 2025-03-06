# src/web/routes/camera.py
from flask import Blueprint, jsonify, request, Response, current_app
from ..utils.camera import run_camera_action, generate_camera_frames
from ..utils.files import read_csv_settings, write_csv_settings
from ..error_handlers import APIError, ErrorCode
from .api import create_success_response
from ..config import CAMERA_SETTINGS_FILE

# Create blueprint
camera_bp = Blueprint('camera', __name__, url_prefix='/api/camera')

@camera_bp.route('/settings', methods=['GET'])
def get_camera_settings():
    """Get camera settings."""
    settings = read_csv_settings(CAMERA_SETTINGS_FILE)
    return jsonify(settings)

@camera_bp.route('/settings', methods=['POST'])
def update_camera_settings():
    """Update camera settings."""
    settings = request.get_json()
    success = write_csv_settings(CAMERA_SETTINGS_FILE, settings)
    
    if success:
        return jsonify(create_success_response(message='Camera settings updated'))
    else:
        raise APIError(
            ErrorCode.UNKNOWN_ERROR,
            "Failed to update camera settings"
        )

@camera_bp.route('/calibrate', methods=['POST'])
def calibrate_camera():
    """Run camera calibration."""
    try:
        success, output = run_camera_action('calibrate')
        
        if success:
            return jsonify(create_success_response(
                data={'output': output},
                message='Camera calibrated successfully'
            ))
        else:
            raise APIError(
                ErrorCode.CAMERA_ERROR,
                "Calibration failed",
                {"output": output}
            )
    except APIError:
        raise
    except Exception as e:
        current_app.logger.error(f"Error during camera calibration: {str(e)}")
        raise APIError(
            ErrorCode.CAMERA_ERROR,
            "Calibration failed",
            {"error": str(e)}
        )

@camera_bp.route('/capture', methods=['POST'])
def capture_photo():
    """Capture a photo."""
    try:
        success, output = run_camera_action('capture')
        
        if success:
            return jsonify(create_success_response(
                data={'output': output},
                message='Photo captured successfully'
            ))
        else:
            raise APIError(
                ErrorCode.CAMERA_ERROR,
                "Photo capture failed",
                {"output": output}
            )
    except APIError:
        raise
    except Exception as e:
        current_app.logger.error(f"Error capturing photo: {str(e)}")
        raise APIError(
            ErrorCode.CAMERA_ERROR,
            "Photo capture failed",
            {"error": str(e)}
        )

@camera_bp.route('/stream')
def camera_stream():
    """Stream camera frames."""
    return Response(
        generate_camera_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )
