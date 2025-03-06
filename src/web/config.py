import os
import logging
from pathlib import Path

class Config:
    """Base configuration class for CreatureBox web interface."""
    
    # Directories
    BASE_DIR = Path(__file__).resolve().parent.parent
    WEB_DIR = BASE_DIR / 'web'
    STATIC_DIR = WEB_DIR / 'static'
    PHOTOS_DIR = BASE_DIR / 'photos'
    LOGS_DIR = BASE_DIR / 'logs'
    
    # Web Server Configuration
    WEB_HOST = os.getenv('CREATUREBOX_HOST', '0.0.0.0')
    WEB_PORT = int(os.getenv('CREATUREBOX_PORT', 5000))
    
    # Logging Configuration
    LOGGING_LEVEL = os.getenv('CREATUREBOX_LOG_LEVEL', 'INFO')
    LOGGING_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Feature Flags
    FEATURES = {
        'camera_streaming': os.getenv('FEATURE_CAMERA_STREAM', 'true').lower() == 'true',
        'photo_gallery': os.getenv('FEATURE_PHOTO_GALLERY', 'true').lower() == 'true',
        'network_settings': os.getenv('FEATURE_NETWORK_SETTINGS', 'true').lower() == 'true'
    }
    
    # Storage Configurations
    MAX_PHOTO_STORAGE_GB = int(os.getenv('MAX_PHOTO_STORAGE', 16))
    BACKUP_STORAGE_THRESHOLD_GB = int(os.getenv('BACKUP_STORAGE_THRESHOLD', 4))
    
    # Security Settings
    SECRET_KEY = os.getenv('CREATUREBOX_SECRET_KEY', 'development_secret_key')
    
    @classmethod
    def configure_logging(cls):
        """Configure logging based on configuration."""
        logging.basicConfig(
            level=getattr(logging, cls.LOGGING_LEVEL.upper()),
            format=cls.LOGGING_FORMAT,
            handlers=[
                logging.FileHandler(cls.LOGS_DIR / 'creaturebox_web.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger('creaturebox')

# Instantiate logger
logger = Config.configure_logging()