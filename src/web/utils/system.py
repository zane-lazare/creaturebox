# src/web/utils/system.py
import os
import sys
import subprocess
import logging
import time
import re
import psutil
from ..error_handlers import APIError, ErrorCode

logger = logging.getLogger(__name__)

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
        if hasattr(psutil, 'cpu_percent'):
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
        control_values = read_control_values()
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

def detect_pi_model():
    """Detect Raspberry Pi model."""
    model = "unknown"
    
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            
        if "Raspberry Pi 5" in cpuinfo:
            model = "5"
        elif "Raspberry Pi 4" in cpuinfo:
            model = "4"
        elif "Raspberry Pi" in cpuinfo:
            model = "other"
    except Exception as e:
        logger.error(f"Error detecting Pi model: {str(e)}")
    
    return model

def read_control_values(file_path=None):
    """Read key-value pairs from the control file."""
    from ..config import CONTROLS_FILE
    
    if file_path is None:
        file_path = CONTROLS_FILE
    
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

def write_control_values(values, file_path=None):
    """Write key-value pairs to the control file."""
    from ..config import CONTROLS_FILE
    
    if file_path is None:
        file_path = CONTROLS_FILE
    
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
    from ..config import SCRIPTS_DIR
    
    try:
        script_path = os.path.join(SCRIPTS_DIR, script_name)
        cmd = ['python3', script_path]
        if args:
            cmd.extend(args)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error running script {script_name}: {result.stderr}")
            raise APIError(
                ErrorCode.SYSTEM_COMMAND_FAILED, 
                f"Failed to run script: {script_name}",
                {"stderr": result.stderr}
            )
        
        return True, result.stdout
    except subprocess.SubprocessError as e:
        logger.error(f"Subprocess error running script {script_name}: {str(e)}")
        raise APIError(
            ErrorCode.SYSTEM_COMMAND_FAILED,
            f"Subprocess error running script: {script_name}",
            {"error": str(e)}
        )
    except Exception as e:
        logger.error(f"Exception running script {script_name}: {str(e)}")
        raise APIError(
            ErrorCode.SYSTEM_COMMAND_FAILED,
            f"Error running script: {script_name}",
            {"error": str(e)}
        )

def get_power_info():
    """Get power information."""
    try:
        # Determine Raspberry Pi model
        pi_model = detect_pi_model()
        
        # Default values
        source = 'External Power'
        battery_level = 100
        voltage = 5.0
        current = 0
        
        # Check for PiJuice on Pi 4
        if pi_model == '4':
            try:
                # Dynamically import PiJuice to avoid import errors on systems without it
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
    from ..config import BASE_DIR, SCHEDULE_SETTINGS_FILE
    from .files import read_csv_settings
    
    try:
        # Read schedule settings
        schedule_settings = read_csv_settings(SCHEDULE_SETTINGS_FILE)
        
        # Read control values
        control_values = read_control_values()
        
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
            
            for root, dirs, files in os.walk(os.path.join(BASE_DIR, 'photos')):
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
