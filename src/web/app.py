#!/usr/bin/env python3
"""
CreatureBox Web Interface Backend
--------------------------------

This Flask application provides a web interface for the CreatureBox system.
It allows users to view the camera feed, configure settings, and manage photos.
"""

import os
import csv
import json
import time
import logging
import subprocess
from datetime import datetime
from flask import Flask, jsonify, request, render_template, send_file, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename
import io
import threading

# Try to import optional components with fallbacks
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("OpenCV not available. Camera streaming will be disabled.")

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("psutil not available. Some system stats will be estimated.")

# Configure logging
LOG_DIR = os.path.expanduser("~/CreatureBox/logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=os.path.join(LOG_DIR, 'creaturebox_web.log')
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)  # Enable Cross-Origin Resource Sharing

# Configuration - All paths relative to user's home
HOME_DIR = os.path.expanduser("~")
BASE_DIR = os.path.join(HOME_DIR, "CreatureBox")
PHOTOS_DIR = os.path.join(BASE_DIR, "photos")
SCRIPTS_DIR = os.path.join(BASE_DIR, "Software")
CONFIG_DIR = BASE_DIR
CAMERA_SETTINGS_FILE = os.path.join(CONFIG_DIR, "camera_settings.csv")
SCHEDULE_SETTINGS_FILE = os.path.join(CONFIG_DIR, "schedule_settings.csv")
CONTROLS_FILE = os.path.join(CONFIG_DIR, "controls.txt")

# Create necessary directories if they don't exist
os.makedirs(PHOTOS_DIR, exist_ok=True)

# Global variables
camera = None
camera_lock = threading.Lock() if CV2_AVAILABLE else None

# Utility functions
def read_csv_settings(file_path):
    """Read settings from a CSV file."""
    settings = {}
    try:
        with open(file_path, 'r') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                settings[row['SETTING']] = row['VALUE']
        return settings
    except Exception as e:
        logger.error(f"Error reading CSV file {file_path}: {str(e)}")
        return {}

def write_csv_settings(file_path, settings):
    """Write settings to a CSV file."""
    try:
        # First read existing settings to preserve structure
        existing_settings = []
        with open(file_path, 'r') as csv_file:
            reader = csv.DictReader(csv_file)
            fieldnames = reader.fieldnames
            for row in reader:
                existing_settings.append(row)
        
        # Update settings
        for row in existing_settings:
            if row['SETTING'] in settings:
                row['VALUE'] = settings[row['SETTING']]
        
        # Write back to file
        with open(file_path, 'w', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(existing_settings)
        
        return True
    except Exception as e:
        logger.error(f"Error writing CSV file {file_path}: {str(e)}")
        return False

def read_control_values(file_path):
    """Read key-value pairs from the control file."""
    control_values = {}
    try:
        with open(file_path, 'r') as file:
            for line in file:
                key, value = line.strip().split('=')
                control_values[key] = value
        return control_values
    except Exception as e:
        logger.error(f"Error reading control file {file_path}: {str(e)}")
        return {}

def write_control_values(file_path, values):
    """Write key-value pairs to the control file."""
    try:
        # First read existing values to preserve structure
        existing_values = []
        with open(file_path, 'r') as file:
            for line in file:
                existing_values.append(line.strip())
        
        # Update values
        for i, line in enumerate(existing_values):
            key, _ = line.split('=')
            if key in values:
                existing_values[i] = f"{key}={values[key]}"
        
        # Write back to file
        with open(file_path, 'w') as file:
            for line in existing_values:
                file.write(f"{line}\n")
        
        return True
    except Exception as e:
        logger.error(f"Error writing control file {file_path}: {str(e)}")
        return False

def run_script(script_name, args=None):
    """Run a script and return the result."""
    try:
        script_path = os.path.join(SCRIPTS_DIR, script_name)
        cmd = ['python3', script_path]
        if args:
            cmd.extend(args)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error running script {script_name}: {result.stderr}")
            return False, result.stderr
        
        return True, result.stdout
    except Exception as e:
        logger.error(f"Exception running script {script_name}: {str(e)}")
        return False, str(e)

def get_system_info():
    """Get system information."""
    try:
        # Get CPU temperature
        temp = 0
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = float(f.read()) / 1000.0
        except:
            temp = 45.0  # Fallback value
        
        # Get CPU usage and memory usage
        if PSUTIL_AVAILABLE:
            cpu_usage = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            uptime = time.time() - psutil.boot_time()
        else:
            # Fallback values if psutil isn't available
            cpu_usage = 25.0
            memory_usage = 40.0
            uptime = 3600  # Assume 1 hour
        
        # Get device name
        control_values = read_control_values(CONTROLS_FILE)
        device_name = control_values.get('name', 'CreatureBox')
        
        # Determine status
        if temp > 80:
            status = 'Warning'
        else:
            status = 'Online'
        
        return {
            'cpuTemp': round(temp, 1),
            'cpuUsage': round(cpu_usage, 1),
            'memoryUsage': round(memory_usage, 1),
            'uptime': int(uptime),
            'deviceName': device_name,
            'status': status
        }
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
        return {
            'cpuTemp': 45.0,
            'cpuUsage': 25.0,
            'memoryUsage': 40.0,
            'uptime': 3600,
            'deviceName': 'CreatureBox',
            'status': 'Error'
        }

def get_storage_info():
    """Get storage information."""
    try:
        # Get internal storage info
        internal_stat = os.statvfs(BASE_DIR)
        internal_total = internal_stat.f_blocks * internal_stat.f_bsize
        internal_free = internal_stat.f_bfree * internal_stat.f_bsize
        internal_used = internal_total - internal_free
        
        # Get photos count and size
        photos_count = 0
        photos_size = 0
        
        for root, dirs, files in os.walk(PHOTOS_DIR):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                    photos_count += 1
                    photos_size += os.path.getsize(os.path.join(root, file))
        
        # Check for external storage
        external_connected = False
        external_total = 0
        external_used = 0
        
        # Look for external drives
        for path in ['/media', '/mnt']:
            if os.path.exists(path):
                for username in os.listdir(path):
                    user_path = os.path.join(path, username)
                    if os.path.isdir(user_path):
                        for mount_point in os.listdir(user_path):
                            mount_path = os.path.join(user_path, mount_point)
                            if os.path.ismount(mount_path):
                                external_connected = True
                                stat = os.statvfs(mount_path)
                                external_total = stat.f_blocks * stat.f_bsize
                                external_free = stat.f_bfree * stat.f_bsize
                                external_used = external_total - external_free
                                break
        
        return {
            'internalTotal': internal_total,
            'internalUsed': internal_used,
            'externalConnected': external_connected,
            'externalTotal': external_total,
            'externalUsed': external_used,
            'photosCount': photos_count,
            'photosSize': photos_size
        }
    except Exception as e:
        logger.error(f"Error getting storage info: {str(e)}")
        return {
            'internalTotal': 0,
            'internalUsed': 0,
            'externalConnected': False,
            'externalTotal': 0,
            'externalUsed': 0,
            'photosCount': 0,
            'photosSize': 0
        }

def get_power_info():
    """Get power information."""
    try:
        # Determine Raspberry Pi model
        pi_model = None
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if line.startswith('Model'):
                    if 'Pi 4' in line:
                        pi_model = '4'
                    elif 'Pi 5' in line:
                        pi_model = '5'
                    break
        
        # Check for PiJuice
        has_pijuice = False
        battery_level = 0
        current = 0
        voltage = 0
        source = 'Unknown'
        
        if pi_model == '4':
            try:
                from pijuice import PiJuice
                pj = PiJuice(1, 0x14)
                status = pj.status.GetStatus()
                if status['error'] == 'NO_ERROR':
                    has_pijuice = True
                    battery_level = pj.status.GetChargeLevel()['data']
                    voltage = pj.status.GetBatteryVoltage()['data'] / 1000.0  # Convert to volts
                    current = pj.status.GetBatteryCurrent()['data']
                    
                    if status['data']['powerInput'] == 'PRESENT':
                        source = 'External Power'
                    else:
                        source = 'Battery'
            except Exception as e:
                logger.error(f"Error getting PiJuice info: {str(e)}")
        
        if not has_pijuice:
            # Default values when no PiJuice is available
            source = 'External Power'
            battery_level = 100
            voltage = 5.0
            current = 0
        
        return {
            'source': source,
            'batteryLevel': battery_level,
            'current': current,
            'voltage': voltage
        }
    except Exception as e:
        logger.error(f"Error getting power info: {str(e)}")
        return {
            'source': 'External Power',
            'batteryLevel': 100,
            'current': 0,
            'voltage': 5.0
        }

def get_schedule_info():
    """Get schedule information."""
    try:
        # Read schedule settings
        schedule_settings = read_csv_settings(SCHEDULE_SETTINGS_FILE)
        
        # Read control values
        control_values = read_control_values(CONTROLS_FILE)
        
        # Determine mode
        mode = 'Unknown'
        if os.path.exists(os.path.join(BASE_DIR, '.debug_mode')):
            mode = 'DEBUG'
        elif os.path.exists(os.path.join(BASE_DIR, '.off_mode')):
            mode = 'OFF'
        else:
            mode = 'ARMED'
        
        # Get next wake time
        next_wake = 0
        try:
            with open('/sys/class/rtc/rtc0/wakealarm', 'r') as f:
                next_wake = int(f.read().strip())
        except:
            pass
        
        # Get last photo time
        last_photo = 0
        try:
            newest_file = None
            newest_time = 0
            
            for root, dirs, files in os.walk(PHOTOS_DIR):
                for file in files:
                    if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                        file_path = os.path.join(root, file)
                        file_time = os.path.getmtime(file_path)
                        if file_time > newest_time:
                            newest_time = file_time
                            newest_file = file_path
            
            if newest_file:
                last_photo = int(newest_time)
        except:
            pass
        
        return {
            'mode': mode,
            'nextWake': next_wake,
            'lastPhoto': last_photo,
            'runtime': schedule_settings.get('runtime', '0')
        }
    except Exception as e:
        logger.error(f"Error getting schedule info: {str(e)}")
        return {
            'mode': 'Unknown',
            'nextWake': 0,
            'lastPhoto': 0,
            'runtime': '0'
        }

def get_photo_dates():
    """Get list of dates with photos."""
    dates = set()
    
    try:
        for root, dirs, files in os.walk(PHOTOS_DIR):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                    # Get file date from directory name
                    dir_name = os.path.basename(root)
                    if dir_name.startswith('20') and len(dir_name) == 10:  # YYYY-MM-DD format
                        dates.add(dir_name)
    except Exception as e:
        logger.error(f"Error getting photo dates: {str(e)}")
    
    return sorted(list(dates), reverse=True)

def get_photos(date=None):
    """Get list of photos, optionally filtered by date."""
    photos = []
    
    try:
        for root, dirs, files in os.walk(PHOTOS_DIR):
            dir_name = os.path.basename(root)
            
            # Skip if filtering by date and this directory doesn't match
            if date and dir_name != date:
                continue
            
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                    file_path = os.path.join(root, file)
                    
                    # Extract metadata
                    file_date = dir_name
                    file_time = '00:00:00'
                    exposure = 0
                    focus = 0
                    
                    # Try to extract time from filename (format: devicename_YYYY_MM_DD__HH_MM_SS_HDRx.jpg)
                    parts = file.split('_')
                    if len(parts) >= 6:
                        try:
                            file_time = f"{parts[3]}:{parts[4]}:{parts[5].split('.')[0]}"
                        except:
                            pass
                    
                    photos.append({
                        'filename': file,
                        'url': f"/api/gallery/photos/view/{file_date}/{file}",
                        'thumbnailUrl': f"/api/gallery/photos/thumbnail/{file_date}/{file}",
                        'date': file_date,
                        'time': file_time,
                        'exposure': exposure,
                        'focus': focus
                    })
    except Exception as e:
        logger.error(f"Error getting photos: {str(e)}")
    
    # Sort by date and time, newest first
    photos.sort(key=lambda x: (x['date'], x['time']), reverse=True)
    
    return photos

def get_photo_file(date, filename):
    """Get a photo file."""
    try:
        file_path = os.path.join(PHOTOS_DIR, date, secure_filename(filename))
        if os.path.exists(file_path):
            return file_path
        return None
    except Exception as e:
        logger.error(f"Error getting photo file: {str(e)}")
        return None

def generate_thumbnail(file_path, size=(200, 200)):
    """Generate a thumbnail for an image."""
    if not CV2_AVAILABLE:
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

def get_log_content(log_type):
    """Get log content."""
    try:
        log_file = None
        
        if log_type == 'system':
            # Use system logs
            cmd = ['journalctl', '-n', '100']
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.stdout
        elif log_type == 'camera':
            # Use camera logs
            log_file = os.path.join(BASE_DIR, 'logs', 'camera.log')
        elif log_type == 'scheduler':
            # Use scheduler logs
            log_file = os.path.join(BASE_DIR, 'logs', 'scheduler.log')
        elif log_type == 'power':
            # Use power logs
            log_file = os.path.join(BASE_DIR, 'logs', 'power.log')
        
        if log_file and os.path.exists(log_file):
            with open(log_file, 'r') as f:
                return f.read()
        
        return f"No {log_type} logs available"
    except Exception as e:
        logger.error(f"Error reading log content: {str(e)}")
        return f"Error reading logs: {str(e)}"

def init_camera():
    """Initialize the camera."""
    global camera
    if not CV2_AVAILABLE:
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
    if not CV2_AVAILABLE:
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
    
    if not CV2_AVAILABLE:
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

# API Routes
@app.route('/')
def index():
    """Serve the main HTML page."""
    return app.send_static_file('index.html')

@app.route('/api/system/status')
def system_status():
    """Get system status information."""
    system_info = get_system_info()
    power_info = get_power_info()
    storage_info = get_storage_info()
    schedule_info = get_schedule_info()
    
    return jsonify({
        'system': system_info,
        'power': power_info,
        'storage': storage_info,
        'schedule': schedule_info
    })

@app.route('/api/camera/settings', methods=['GET'])
def get_camera_settings():
    """Get camera settings."""
    settings = read_csv_settings(CAMERA_SETTINGS_FILE)
    return jsonify(settings)

@app.route('/api/camera/settings', methods=['POST'])
def update_camera_settings():
    """Update camera settings."""
    settings = request.get_json()
    success = write_csv_settings(CAMERA_SETTINGS_FILE, settings)
    
    if success:
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to update camera settings'}), 500

@app.route('/api/camera/calibrate', methods=['POST'])
def calibrate_camera():
    """Run camera calibration."""
    success, output = run_script('TakePhoto.py', ['--calibrate'])
    
    if success:
        return jsonify({'status': 'success', 'output': output})
    else:
        return jsonify({'status': 'error', 'message': f'Calibration failed: {output}'}), 500

@app.route('/api/camera/capture', methods=['POST'])
def capture_photo():
    """Capture a photo."""
    success, output = run_script('TakePhoto.py')
    
    if success:
        return jsonify({'status': 'success', 'output': output})
    else:
        return jsonify({'status': 'error', 'message': f'Capture failed: {output}'}), 500

@app.route('/api/camera/stream')
def camera_stream():
    """Stream camera frames."""
    return Response(generate_camera_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/schedule/settings', methods=['GET'])
def get_schedule_settings():
    """Get schedule settings."""
    settings = read_csv_settings(SCHEDULE_SETTINGS_FILE)
    return jsonify(settings)

@app.route('/api/schedule/settings', methods=['POST'])
def update_schedule_settings():
    """Update schedule settings."""
    settings = request.get_json()
    success = write_csv_settings(SCHEDULE_SETTINGS_FILE, settings)
    
    # Also update runtime in control file if present
    if 'runtime' in settings:
        control_values = {'runtime': settings['runtime']}
        write_control_values(CONTROLS_FILE, control_values)
    
    if success:
        # Run scheduler script to apply new settings
        run_script('Scheduler.py')
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to update schedule settings'}), 500

@app.route('/api/network/status')
def network_status():
    """Get network status."""
    try:
        # Run iwconfig to get WiFi info
        wifi_info = subprocess.run(['iwconfig'], capture_output=True, text=True).stdout
        
        # Parse output
        ssid = None
        signal_strength = 0
        connected = False
        
        for line in wifi_info.split('\n'):
            if 'ESSID:' in line:
                ssid_part = line.split('ESSID:')[1].strip('"')
                if ssid_part != 'off/any':
                    ssid = ssid_part
                    connected = True
            elif 'Signal level=' in line:
                try:
                    signal_part = line.split('Signal level=')[1].split(' ')[0]
                    # Convert dBm to percentage (rough approximation)
                    if 'dBm' in signal_part:
                        dbm = int(signal_part.replace('dBm', ''))
                        # Convert dBm to percentage (typical range: -100 dBm to -50 dBm)
                        signal_strength = min(100, max(0, int((dbm + 100) * 2)))
                    else:
                        signal_strength = int(signal_part)
                except:
                    pass
        
        # Get IP address
        ip_info = subprocess.run(['hostname', '-I'], capture_output=True, text=True).stdout
        ip = ip_info.strip().split(' ')[0] if ip_info.strip() else 'Not available'
        
        return jsonify({
            'connected': connected,
            'ssid': ssid,
            'ip': ip,
            'signalStrength': signal_strength
        })
    except Exception as e:
        logger.error(f"Error getting network status: {str(e)}")
        return jsonify({
            'connected': False,
            'ssid': None,
            'ip': 'Not available',
            'signalStrength': 0
        })

@app.route('/api/network/add', methods=['POST'])
def add_network():
    """Add a new WiFi network."""
    data = request.get_json()
    
    if 'ssid' not in data or 'wifipass' not in data:
        return jsonify({'status': 'error', 'message': 'SSID and password required'}), 400
    
    # Update schedule settings file with new WiFi credentials
    settings = {
        'ssid': data['ssid'],
        'wifipass': data['wifipass']
    }
    
    success = write_csv_settings(SCHEDULE_SETTINGS_FILE, settings)
    
    if success:
        # Run RegisterNewWifi.sh script
        subprocess.Popen(['sudo', os.path.join(SCRIPTS_DIR, 'RegisterNewWifi.sh')])
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to add network'}), 500

@app.route('/api/gallery/dates')
def gallery_dates():
    """Get list of dates with photos."""
    dates = get_photo_dates()
    return jsonify(dates)

@app.route('/api/gallery/photos')
def gallery_photos():
    """Get list of photos."""
    date = request.args.get('date')
    photos = get_photos(date)
    return jsonify(photos)

@app.route('/api/gallery/photos/view/<date>/<filename>')
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
        return 'Photo not found', 404

@app.route('/api/gallery/photos/thumbnail/<date>/<filename>')
def view_thumbnail(date, filename):
    """View a photo thumbnail."""
    file_path = get_photo_file(date, filename)
    
    if file_path:
        thumbnail = generate_thumbnail(file_path)
        if thumbnail is not None:
            return Response(thumbnail.tobytes(), mimetype='image/jpeg')
    
    return 'Thumbnail not available', 404

@app.route('/api/gallery/photos/<filename>', methods=['DELETE'])
def delete_photo(filename):
    """Delete a photo."""
    try:
        # Find the photo in all date directories
        for root, dirs, files in os.walk(PHOTOS_DIR):
            if filename in files:
                file_path = os.path.join(root, filename)
                os.remove(file_path)
                return jsonify({'status': 'success'})
        
        return jsonify({'status': 'error', 'message': 'Photo not found'}), 404
    except Exception as e:
        logger.error(f"Error deleting photo: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Error deleting photo: {str(e)}'}), 500

@app.route('/api/logs/<log_type>')
def logs(log_type):
    """Get log content."""
    content = get_log_content(log_type)
    return jsonify({'content': content})

@app.route('/api/logs/<log_type>/download')
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

@app.route('/api/system/toggle-lights', methods=['POST'])
def toggle_lights():
    """Toggle attraction lights."""
    try:
        # Check current state by reading control file
        control_values = read_control_values(CONTROLS_FILE)
        current_state = control_values.get('lights_on', 'false').lower() == 'true'
        
        # Toggle state
        new_state = not current_state
        
        # Run appropriate script
        if new_state:
            success, _ = run_script('Attract_On.py')
        else:
            success, _ = run_script('Attract_Off.py')
        
        # Update control file
        write_control_values(CONTROLS_FILE, {'lights_on': str(new_state).lower()})
        
        return jsonify({'status': 'success', 'lightsOn': new_state})
    except Exception as e:
        logger.error(f"Error toggling lights: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Error toggling lights: {str(e)}'}), 500

@app.route('/api/system/reboot', methods=['POST'])
def reboot_system():
    """Reboot the system."""
    try:
        # Run reboot command in background
        subprocess.Popen(['sudo', 'reboot'])
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error rebooting system: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Error rebooting system: {str(e)}'}), 500

@app.route('/api/system/shutdown', methods=['POST'])
def shutdown_system():
    """Shut down the system."""
    try:
        # Run shutdown command in background
        subprocess.Popen(['sudo', 'shutdown', '-h', 'now'])
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error shutting down system: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Error shutting down system: {str(e)}'}), 500

@app.route('/api/system/power', methods=['GET'])
def get_power_settings():
    """Get power settings."""
    try:
        # Determine Raspberry Pi model
        pi_model = None
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if line.startswith('Model'):
                    if 'Pi 4' in line:
                        pi_model = '4'
                    elif 'Pi 5' in line:
                        pi_model = '5'
                    break
        
        # Read EEPROM settings for Pi 5
        eeprom_settings = {}
        power_manager = 'Unknown'
        
        if pi_model == '5':
            try:
                # Run rpi-eeprom-config command
                result = subprocess.run(['sudo', 'rpi-eeprom-config'], capture_output=True, text=True)
                
                for line in result.stdout.split('\n'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        eeprom_settings[key] = value
                
                power_manager = 'Raspberry Pi EEPROM'
            except:
                pass
        elif pi_model == '4':
            try:
                from pijuice import PiJuice
                pj = PiJuice(1, 0x14)
                status = pj.status.GetStatus()
                if status['error'] == 'NO_ERROR':
                    power_manager = 'PiJuice'
            except:
                power_manager = 'Unknown'
        
        return jsonify({
            'piModel': pi_model,
            'powerManager': power_manager,
            'POWER_OFF_ON_HALT': eeprom_settings.get('POWER_OFF_ON_HALT', '0'),
            'WAKE_ON_GPIO': eeprom_settings.get('WAKE_ON_GPIO', '0')
        })
    except Exception as e:
        logger.error(f"Error getting power settings: {str(e)}")
        return jsonify({
            'piModel': 'Unknown',
            'powerManager': 'Unknown',
            'POWER_OFF_ON_HALT': '0',
            'WAKE_ON_GPIO': '0'
        })

@app.route('/api/system/power', methods=['POST'])
def update_power_settings():
    """Update power settings."""
    try:
        data = request.get_json()
        
        # Determine Raspberry Pi model
        pi_model = None
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if line.startswith('Model'):
                    if 'Pi 4' in line:
                        pi_model = '4'
                    elif 'Pi 5' in line:
                        pi_model = '5'
                    break
        
        # Only update EEPROM settings on Pi 5
        if pi_model == '5':
            settings = {}
            
            if 'POWER_OFF_ON_HALT' in data:
                settings['POWER_OFF_ON_HALT'] = data['POWER_OFF_ON_HALT']
            
            if 'WAKE_ON_GPIO' in data:
                settings['WAKE_ON_GPIO'] = data['WAKE_ON_GPIO']
            
            # Create temporary config file
            with open('/tmp/eeprom_config.txt', 'w') as f:
                for key, value in settings.items():
                    f.write(f"{key}={value}\n")
            
            # Apply settings
            subprocess.run(['sudo', 'rpi-eeprom-config', '--apply', '/tmp/eeprom_config.txt'], check=True)
        
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error updating power settings: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Error updating power settings: {str(e)}'}), 500

# Main entry point
if __name__ == '__main__':
    try:
        # Create required directories if they don't exist
        os.makedirs(PHOTOS_DIR, exist_ok=True)
        
        # Start the server
        app.run(host='0.0.0.0', port=5000, threaded=True)
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
    finally:
        # Ensure camera is released
        release_camera()
