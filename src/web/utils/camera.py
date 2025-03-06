# src/web/utils/camera.py
import os
import time
import logging
import threading
import cv2
import numpy as np
from ..error_handlers import APIError, ErrorCode

logger = logging.getLogger(__name__)

# Global variables for camera access
camera = None
camera_lock = threading.Lock()

def init_camera():
    """Initialize the camera."""
    global camera
    
    # Check if OpenCV is available
    if not 'cv2' in globals():
        logger.error("OpenCV not available. Camera operations disabled.")
        return False
    
    try:
        with camera_lock:
            if camera is not None:
                camera.release()
            
            camera = cv2.VideoCapture(0)
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            if not camera.isOpened():
                logger.error("Failed to open camera")
                camera = None
                return False
            
            return True
    except Exception as e:
        logger.error(f"Error initializing camera: {str(e)}")
        camera = None
        return False

def release_camera():
    """Release the camera."""
    global camera
    
    # Check if OpenCV is available
    if not 'cv2' in globals():
        return
    
    try:
        with camera_lock:
            if camera is not None:
                camera.release()
                camera = None
    except Exception as e:
        logger.error(f"Error releasing camera: {str(e)}")

def generate_camera_frames():
    """Generate camera frames for streaming."""
    global camera
    
    # Check if OpenCV is available
    if not 'cv2' in globals():
        yield (b'--frame\r\n'
               b'Content-Type: text/plain\r\n\r\n'
               b'Camera not available - OpenCV not installed\r\n')
        return
    
    if not init_camera():
        yield (b'--frame\r\n'
               b'Content-Type: text/plain\r\n\r\n'
               b'Camera not available - Failed to initialize\r\n')
        return
    
    try:
        while True:
            with camera_lock:
                if camera is None:
                    break
                
                success, frame = camera.read()
                if not success:
                    break
                
                # Encode frame as JPEG
                _, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()
                
                # Yield frame in MJPEG format
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
                # Add a small delay to control frame rate
                time.sleep(0.1)
    except Exception as e:
        logger.error(f"Error generating camera frames: {str(e)}")
    finally:
        release_camera()

def generate_thumbnail(file_path, size=(200, 200)):
    """Generate a thumbnail for an image."""
    # Check if OpenCV is available
    if not 'cv2' in globals():
        return None
    
    try:
        img = cv2.imread(file_path)
        if img is None:
            return None
        
        # Resize image
        height, width = img.shape[:2]
        if width > height:
            new_width = size[0]
            new_height = int(height * (new_width / width))
        else:
            new_height = size[1]
            new_width = int(width * (new_height / height))
        
        img = cv2.resize(img, (new_width, new_height))
        
        # Crop to square if needed
        if new_width != new_height:
            if new_width > new_height:
                start_x = (new_width - new_height) // 2
                img = img[:, start_x:start_x + new_height]
            else:
                start_y = (new_height - new_width) // 2
                img = img[start_y:start_y + new_width, :]
        
        # Encode to JPEG
        _, buffer = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        
        return buffer
    except Exception as e:
        logger.error(f"Error generating thumbnail: {str(e)}")
        return None

def run_camera_action(action, args=None):
    """Run a camera-related action script."""
    from .system import run_script
    
    if action == 'calibrate':
        return run_script('TakePhoto.py', ['--calibrate'])
    elif action == 'capture':
        return run_script('TakePhoto.py')
    else:
        raise APIError(
            ErrorCode.INVALID_REQUEST,
            f"Unknown camera action: {action}"
        )
