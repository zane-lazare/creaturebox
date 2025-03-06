# src/web/config.py
import os

# Base Paths
HOME_DIR = os.path.expanduser("~")
BASE_DIR = os.path.join(HOME_DIR, "CreatureBox")
PHOTOS_DIR = os.path.join(BASE_DIR, "photos")
PHOTOS_BACKUP_DIR = os.path.join(BASE_DIR, "photos_backedup")
SCRIPTS_DIR = os.path.join(BASE_DIR, "Software")
CONFIG_DIR = BASE_DIR
LOG_DIR = os.path.join(BASE_DIR, "logs")

# File Paths
CAMERA_SETTINGS_FILE = os.path.join(CONFIG_DIR, "camera_settings.csv")
SCHEDULE_SETTINGS_FILE = os.path.join(CONFIG_DIR, "schedule_settings.csv")
CONTROLS_FILE = os.path.join(CONFIG_DIR, "controls.txt")

# Web Server Settings
PORT = 5000
HOST = '0.0.0.0'
DEBUG = False
THREADED = True

# Feature Flags
ENABLE_CAMERA_STREAM = True
ENABLE_BACKGROUND_JOBS = True
ENABLE_RATE_LIMITING = False  # For future implementation

# Performance Settings
PHOTO_PROCESSING_THREADS = 2
CACHE_TIMEOUT = 300  # seconds
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB

# Thumbnail Settings
THUMBNAIL_SIZE = (200, 200)
THUMBNAIL_QUALITY = 85

# Camera Settings
CAMERA_LOCK_TIMEOUT = 30  # seconds

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = os.path.join(LOG_DIR, 'creaturebox_web.log')

# API Settings
API_RATE_LIMIT = 60  # requests per minute
