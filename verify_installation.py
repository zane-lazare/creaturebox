#!/usr/bin/env python3
"""
CreatureBox Installation Verification Script
-------------------------------------------
This script verifies that the CreatureBox installation is complete and functional.
"""

import os
import sys
import subprocess
import importlib
import json
import logging
import time
import requests
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.expanduser('~/CreatureBox/verify_install.log'))
    ]
)
logger = logging.getLogger(__name__)

# Constants
HOME_DIR = os.path.expanduser('~')
VENV_PATH = os.path.join(HOME_DIR, 'creaturebox-venv')
CREATUREBOX_DIR = os.path.join(HOME_DIR, 'CreatureBox')

class VerificationError(Exception):
    """Exception raised for verification errors."""
    pass

def check_python_environment():
    """Check Python version and virtual environment."""
    logger.info("Checking Python environment...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 7):
        raise VerificationError(f"Python version {python_version.major}.{python_version.minor} is not supported. CreatureBox requires Python 3.7+")
    
    logger.info(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check if we're in the correct virtual environment
    if not os.environ.get('VIRTUAL_ENV') or not os.environ.get('VIRTUAL_ENV').startswith(VENV_PATH):
        logger.warning("Not running in the CreatureBox virtual environment")
        logger.warning(f"Expected: {VENV_PATH}")
        logger.warning(f"Current: {os.environ.get('VIRTUAL_ENV')}")
        return False
    
    logger.info("Running in the correct virtual environment")
    return True

def check_required_packages():
    """Check if required Python packages are installed."""
    logger.info("Checking required Python packages...")
    
    required_packages = [
        'flask',
        'flask_cors',
        'numpy',
        'PIL',  # Pillow
        'piexif',
        'psutil',
        'RPi',  # RPi.GPIO
        'schedule'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            importlib.import_module(package)
            logger.info(f"Package '{package}' is installed")
        except ImportError:
            missing_packages.append(package)
            logger.error(f"Package '{package}' is NOT installed")
    
    if missing_packages:
        logger.error(f"Missing required packages: {', '.join(missing_packages)}")
        return False
    
    logger.info("All required Python packages are installed")
    return True

def check_directory_structure():
    """Check if the CreatureBox directory structure is correct."""
    logger.info("Checking directory structure...")
    
    required_dirs = [
        '',  # Main directory
        'Software',
        'photos',
        'photos_backedup',
        'logs',
        'web',
        'web/static'
    ]
    
    missing_dirs = []
    for dir_name in required_dirs:
        dir_path = os.path.join(CREATUREBOX_DIR, dir_name)
        if not os.path.isdir(dir_path):
            missing_dirs.append(dir_name)
            logger.error(f"Directory '{dir_path}' is missing")
    
    if missing_dirs:
        logger.error(f"Missing required directories: {', '.join(missing_dirs)}")
        return False
    
    logger.info("Directory structure is correct")
    return True

def check_critical_files():
    """Check if critical files exist."""
    logger.info("Checking critical files...")
    
    required_files = [
        'TakePhoto.py',
        'Scheduler.py',
        'camera_settings.csv',
        'schedule_settings.csv',
        'controls.txt',
        'web/app.py'
    ]
    
    missing_files = []
    for file_name in required_files:
        file_path = os.path.join(CREATUREBOX_DIR, file_name)
        if not os.path.isfile(file_path):
            missing_files.append(file_name)
            logger.error(f"File '{file_path}' is missing")
    
    if missing_files:
        logger.error(f"Missing required files: {', '.join(missing_files)}")
        return False
    
    logger.info("All critical files are present")
    return True

def check_permissions():
    """Check if files and directories have correct permissions."""
    logger.info("Checking permissions...")
    
    # Check if scripts are executable
    script_dirs = [
        os.path.join(CREATUREBOX_DIR, 'Software'),
        CREATUREBOX_DIR  # For symlinked scripts
    ]
    
    non_executable_scripts = []
    for script_dir in script_dirs:
        if os.path.isdir(script_dir):
            for file_name in os.listdir(script_dir):
                if file_name.endswith('.py') or file_name.endswith('.sh'):
                    file_path = os.path.join(script_dir, file_name)
                    if os.path.isfile(file_path) and not os.access(file_path, os.X_OK):
                        non_executable_scripts.append(file_path)
                        logger.error(f"Script '{file_path}' is not executable")
    
    if non_executable_scripts:
        logger.error(f"{len(non_executable_scripts)} scripts are not executable")
        return False
    
    logger.info("File permissions are correct")
    return True

def check_system_services():
    """Check if system services are installed and running."""
    logger.info("Checking system services...")
    
    # Check web service
    try:
        result = subprocess.run(['systemctl', 'is-active', 'creaturebox-web.service'], 
                               stdout=subprocess.PIPE, text=True, check=False)
        if result.stdout.strip() == 'active':
            logger.info("Web service is running")
        else:
            logger.error("Web service is not running")
            return False
    except subprocess.CalledProcessError:
        logger.error("Failed to check web service status")
        return False
    
    # Check nginx
    try:
        result = subprocess.run(['systemctl', 'is-active', 'nginx'], 
                               stdout=subprocess.PIPE, text=True, check=False)
        if result.stdout.strip() == 'active':
            logger.info("Nginx service is running")
        else:
            logger.error("Nginx service is not running")
            return False
    except subprocess.CalledProcessError:
        logger.error("Failed to check nginx status")
        return False
    
    # Check if nginx config is valid
    try:
        result = subprocess.run(['sudo', 'nginx', '-t'], 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                               text=True, check=False)
        if result.returncode == 0:
            logger.info("Nginx configuration is valid")
        else:
            logger.error(f"Nginx configuration is invalid: {result.stderr}")
            return False
    except subprocess.CalledProcessError:
        logger.error("Failed to check nginx configuration")
        return False
    
    logger.info("System services are configured correctly")
    return True

def check_web_interface():
    """Check if the web interface is accessible."""
    logger.info("Checking web interface accessibility...")
    
    # Try to connect to the web interface
    try:
        # Try localhost access first
        response = requests.get('http://localhost:5000', timeout=5)
        if response.status_code == 200:
            logger.info("Web interface is accessible via localhost")
            return True
    except requests.RequestException as e:
        logger.warning(f"Could not access web interface via localhost: {e}")
    
    # Try IP address if localhost failed
    try:
        # Get IP address
        ip_result = subprocess.run(['hostname', '-I'], 
                                  stdout=subprocess.PIPE, text=True, check=False)
        ip_address = ip_result.stdout.strip().split()[0]
        
        response = requests.get(f'http://{ip_address}:5000', timeout=5)
        if response.status_code == 200:
            logger.info(f"Web interface is accessible via IP address: {ip_address}")
            return True
    except (requests.RequestException, IndexError, subprocess.SubprocessError) as e:
        logger.error(f"Could not access web interface via IP address: {e}")
    
    logger.error("Web interface is not accessible")
    return False

def check_camera():
    """Check if the camera is accessible using multiple detection methods."""
    logger.info("Checking camera accessibility...")
    
    # Method 1: Check for video devices
    camera_detected = False
    if os.path.exists('/dev/video0'):
        logger.info("Camera device /dev/video0 found")
        camera_detected = True
    
    # Method 2: Try libcamera-hello if available
    if not camera_detected:
        try:
            result = subprocess.run(['libcamera-hello', '--list-cameras'], 
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                   text=True, check=False, timeout=5)
            
            if "Available cameras" in result.stdout and not "No cameras available" in result.stdout:
                logger.info("Camera detected via libcamera-hello")
                camera_detected = True
        except (subprocess.SubprocessError, FileNotFoundError, TimeoutError):
            logger.warning("Could not check camera using libcamera-hello")
    
    # Method 3: Try the traditional vcgencmd method (might not work on newer systems)
    if not camera_detected:
        try:
            result = subprocess.run(['vcgencmd', 'get_camera'], 
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                   text=True, check=False, timeout=3)
            
            if 'detected=1' in result.stdout:
                logger.info("Camera detected via vcgencmd")
                camera_detected = True
            else:
                logger.warning("Camera not detected via vcgencmd")
        except (subprocess.SubprocessError, FileNotFoundError, TimeoutError):
            logger.warning("vcgencmd not available or not working on this system")
    
    # If a camera was detected by any method, try to take a test photo
    if camera_detected:
        test_photo_path = os.path.join(CREATUREBOX_DIR, 'test_photo.jpg')
        try:
            # Use libcamera-still to take a photo with extended timeout
            result = subprocess.run(['libcamera-still', '-o', test_photo_path, '-n', '--immediate'], 
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                  text=True, check=False, timeout=15)
            
            if result.returncode == 0 and os.path.exists(test_photo_path):
                logger.info("Successfully took a test photo")
                # Clean up test photo
                os.remove(test_photo_path)
                return True
            else:
                logger.error(f"Failed to take a test photo: {result.stderr}")
                return False
        except (subprocess.SubprocessError, FileNotFoundError, TimeoutError) as e:
            logger.error(f"Error while testing camera: {e}")
            return False
    
    logger.error("No camera detected by any method")
    return False

def run_verification():
    """Run all verification checks and return overall status."""
    verification_results = {
        "Python Environment": check_python_environment(),
        "Required Packages": check_required_packages(),
        "Directory Structure": check_directory_structure(),
        "Critical Files": check_critical_files(),
        "File Permissions": check_permissions(),
        "System Services": check_system_services(),
        "Web Interface": check_web_interface(),
        "Camera": check_camera()
    }
    
    # Count failures
    failures = sum(1 for result in verification_results.values() if result is False)
    
    logger.info("\n" + "="*50)
    logger.info("VERIFICATION RESULTS:")
    logger.info("="*50)
    
    for check, result in verification_results.items():
        status = "PASS" if result else "FAIL"
        logger.info(f"{check:.<30} {status}")
    
    logger.info("="*50)
    if failures == 0:
        logger.info("OVERALL STATUS: SUCCESS - All checks passed!")
        return True
    else:
        logger.info(f"OVERALL STATUS: FAILED - {failures} check(s) failed")
        return False

def generate_system_info():
    """Generate system information for debugging."""
    logger.info("Generating system information...")
    
    system_info = {}
    
    # OS information
    try:
        with open('/etc/os-release', 'r') as f:
            os_info = {}
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    os_info[key] = value.strip('"')
            system_info['os'] = os_info
    except:
        system_info['os'] = "Could not determine OS information"
    
    # Hardware information
    try:
        result = subprocess.run(['cat', '/proc/cpuinfo'], 
                               stdout=subprocess.PIPE, text=True, check=False)
        system_info['hardware'] = result.stdout
    except:
        system_info['hardware'] = "Could not determine hardware information"
    
    # Python version
    system_info['python_version'] = sys.version
    
    # Environment variables
    system_info['environment_variables'] = {key: value for key, value in os.environ.items() 
                                          if not key.startswith('_')}
    
    # Write to file
    info_path = os.path.join(CREATUREBOX_DIR, 'system_info.json')
    with open(info_path, 'w') as f:
        json.dump(system_info, f, indent=2)
    
    logger.info(f"System information written to {info_path}")
    return info_path

if __name__ == "__main__":
    try:
        # First, make sure we're in the virtual environment
        if not os.environ.get('VIRTUAL_ENV'):
            venv_activate = os.path.join(VENV_PATH, 'bin', 'activate')
            if os.path.exists(venv_activate):
                print(f"This script should be run within the virtual environment.")
                print(f"Please activate it with: source {venv_activate}")
                sys.exit(1)
        
        print("CreatureBox Installation Verification")
        print("====================================")
        print("Running verification checks...")
        
        success = run_verification()
        
        if not success:
            print("\nGenerating system information for troubleshooting...")
            info_path = generate_system_info()
            print(f"System information saved to: {info_path}")
            print("\nPlease check the verification log for details.")
            print(f"Log file: {os.path.join(CREATUREBOX_DIR, 'verify_install.log')}")
            
            print("\nTROUBLESHOOTING SUGGESTIONS:")
            print("1. Ensure the virtual environment is activated:")
            print(f"   source {os.path.join(VENV_PATH, 'bin', 'activate')}")
            print("2. Check service status:")
            print("   sudo systemctl status creaturebox-web.service")
            print("3. Check nginx configuration:")
            print("   sudo nginx -t")
            print("4. Refer to the troubleshooting guide:")
            print(f"   {os.path.join(CREATUREBOX_DIR, 'TROUBLESHOOTING.md')}")
            
            sys.exit(1)
        else:
            print("\nVerification successful! CreatureBox is properly installed and configured.")
            print("\nYou can access the web interface at:")
            print("  - http://creaturebox.local    (from other devices on the network)")
            print("  - http://localhost:5000       (from this device)")
            
            # Try to get IP address
            try:
                ip_result = subprocess.run(['hostname', '-I'], stdout=subprocess.PIPE, text=True)
                ip_address = ip_result.stdout.strip().split()[0]
                print(f"  - http://{ip_address}:5000   (using IP address)")
            except:
                pass
            
            sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}", exc_info=True)
        print(f"An unexpected error occurred: {e}")
        print("Please check the log file for details.")
        sys.exit(1)
