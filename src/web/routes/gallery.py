# src/web/routes/gallery.py
from flask import Blueprint, jsonify, request, send_file, Response, current_app
from ..utils.files import get_photo_dates, get_photos, get_photo_file, delete_photo
from ..utils.camera import generate_thumbnail
from ..error_handlers import APIError, ErrorCode
from .api import create_success_response

# Create blueprint
gallery_bp = Blueprint('gallery', __name__, url_prefix='/api/gallery')

@gallery_bp.route('/dates')
def gallery_dates():
    """Get list of dates with photos."""
    dates = get_photo_dates()
    return jsonify(dates)

@gallery_bp.route('/photos')
def gallery_photos():
    """Get list of photos."""
    date = request.args.get('date')
    photos = get_photos(date)
    return jsonify(photos)

@gallery_bp.route('/photos/view/<date>/<filename>')
def view_photo(date, filename):
    """View a photo."""
    file_path = get_photo_file(date, filename)
    
    if file_path:
        download = request.args.get('download', '0') == '1'
        if download:
            return send_file(file_path, as_attachment=True)
        else:
            return send_file(file_path)
    else:
        raise APIError(
            ErrorCode.FILE_NOT_FOUND,
            f"Photo not found: {filename}"
        )

@gallery_bp.route('/photos/thumbnail/<date>/<filename>')
def view_thumbnail(date, filename):
    """View a photo thumbnail."""
    file_path = get_photo_file(date, filename)
    
    if file_path:
        thumbnail = generate_thumbnail(file_path)
        if thumbnail is not None:
            return Response(thumbnail.tobytes(), mimetype='image/jpeg')
    
    raise APIError(
        ErrorCode.FILE_NOT_FOUND,
        f"Thumbnail not available for: {filename}"
    )

@gallery_bp.route('/photos/<filename>', methods=['DELETE'])
def delete_photo_route(filename):
    """Delete a photo."""
    try:
        success = delete_photo(filename)
        return jsonify(create_success_response(message='Photo deleted successfully'))
    except APIError:
        raise
    except Exception as e:
        current_app.logger.error(f"Error deleting photo: {str(e)}")
        raise APIError(
            ErrorCode.UNKNOWN_ERROR,
            f"Failed to delete photo: {filename}",
            {"error": str(e)}
        )
