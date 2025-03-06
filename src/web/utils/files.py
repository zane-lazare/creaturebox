# src/web/utils/files.py
import os
import shutil
import logging
import subprocess
from datetime import datetime
from werkzeug.utils import secure_filename
from ..error_handlers import APIError, ErrorCode

logger = logging.getLogger(__name__)

def read_csv_settings(file_path):
    """Read settings from a CSV file."""
    import csv
    
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
    import csv
    
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

def get_storage_info():
    """Get storage information."""
    from ..config import BASE_DIR, PHOTOS_DIR
    
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

def create_dated_folder(base_path):
    """
    Creates a folder with the current date in the format YYYY-MM-DD if it doesn't exist.
    """
    now = datetime.now()
    # Standard date format
    date_str = now.strftime("%Y-%m-%d")
    folder_path = os.path.join(base_path, date_str)
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    os.chmod(folder_path, 0o777)  # mode=0o777 for read write for all users
    return folder_path

def get_photo_dates():
    """Get list of dates with photos."""
    from ..config import PHOTOS_DIR
    
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
    from ..config import PHOTOS_DIR
    
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
    from ..config import PHOTOS_DIR
    
    try:
        file_path = os.path.join(PHOTOS_DIR, date, secure_filename(filename))
        if os.path.exists(file_path):
            return file_path
        
        # If the dated folder doesn't exist, try in the main photos directory
        file_path = os.path.join(PHOTOS_DIR, secure_filename(filename))
        if os.path.exists(file_path):
            return file_path
            
        return None
    except Exception as e:
        logger.error(f"Error getting photo file: {str(e)}")
        return None

def delete_photo(filename):
    """Delete a photo."""
    from ..config import PHOTOS_DIR
    
    try:
        # Find the photo in all date directories
        for root, dirs, files in os.walk(PHOTOS_DIR):
            if filename in files:
                file_path = os.path.join(root, filename)
                os.remove(file_path)
                logger.info(f"Deleted photo: {file_path}")
                return True
        
        logger.warning(f"Photo not found for deletion: {filename}")
        raise APIError(ErrorCode.FILE_NOT_FOUND, f"Photo not found: {filename}")
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Error deleting photo: {str(e)}")
        raise APIError(
            ErrorCode.SYSTEM_COMMAND_FAILED,
            f"Failed to delete photo: {filename}",
            {"error": str(e)}
        )

def get_log_content(log_type):
    """Get log content."""
    from ..config import BASE_DIR, LOG_DIR
    
    try:
        log_file = None
        
        if log_type == 'system':
            # Use system logs
            cmd = ['journalctl', '-n', '100']
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.stdout
        elif log_type == 'camera':
            # Use camera logs
            log_file = os.path.join(LOG_DIR, 'camera.log')
        elif log_type == 'scheduler':
            # Use scheduler logs
            log_file = os.path.join(LOG_DIR, 'scheduler.log')
        elif log_type == 'power':
            # Use power logs
            log_file = os.path.join(LOG_DIR, 'power.log')
        elif log_type == 'web':
            # Use web logs
            log_file = os.path.join(LOG_DIR, 'creaturebox_web.log')
        
        if log_file and os.path.exists(log_file):
            with open(log_file, 'r') as f:
                return f.read()
        
        return f"No {log_type} logs available"
    except Exception as e:
        logger.error(f"Error reading log content: {str(e)}")
        return f"Error reading logs: {str(e)}"
