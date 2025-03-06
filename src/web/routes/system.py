# src/web/routes/system.py
from flask import Blueprint, jsonify, request, current_app
from ..utils.system import get_system_info, get_power_info, run_script, get_schedule_info
from ..utils.files import get_storage_info
from ..error_handlers import APIError, ErrorCode
from .api import create_success_response

# Create blueprint
system_bp = Blueprint('system', __name__, url_prefix='/api/system')

@system_bp.route('/status')
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

@system_bp.route('/reboot', methods=['POST'])
def reboot_system():
    """Reboot the system."""
    try:
        # Run reboot command in background
        run_script('reboot_system.py')
        return jsonify(create_success_response(message='System is rebooting'))
    except Exception as e:
        current_app.logger.error(f"Error rebooting system: {str(e)}")
        raise APIError(
            ErrorCode.SYSTEM_COMMAND_FAILED,
            "Failed to reboot system",
            {"error": str(e)}
        )

@system_bp.route('/shutdown', methods=['POST'])
def shutdown_system():
    """Shut down the system."""
    try:
        # Run shutdown command in background
        run_script('TurnEverythingOff.py')
        return jsonify(create_success_response(message='System is shutting down'))
    except Exception as e:
        current_app.logger.error(f"Error shutting down system: {str(e)}")
        raise APIError(
            ErrorCode.SYSTEM_COMMAND_FAILED,
            "Failed to shut down system",
            {"error": str(e)}
        )

@system_bp.route('/toggle-lights', methods=['POST'])
def toggle_lights():
    """Toggle attraction lights."""
    from ..utils.system import read_control_values, write_control_values
    
    try:
        # Check current state by reading control file
        control_values = read_control_values()
        current_state = control_values.get('lights_on', 'false').lower() == 'true'
        
        # Toggle state
        new_state = not current_state
        
        # Run appropriate script
        if new_state:
            success, _ = run_script('Attract_On.py')
        else:
            success, _ = run_script('Attract_Off.py')
        
        # Update control file
        write_control_values({'lights_on': str(new_state).lower()})
        
        return jsonify(create_success_response(
            data={'lightsOn': new_state},
            message=f"Lights {'turned on' if new_state else 'turned off'}"
        ))
    except Exception as e:
        current_app.logger.error(f"Error toggling lights: {str(e)}")
        raise APIError(
            ErrorCode.SYSTEM_COMMAND_FAILED,
            "Failed to toggle lights",
            {"error": str(e)}
        )

@system_bp.route('/power', methods=['GET'])
def get_power_settings():
    """Get power settings."""
    from ..utils.system import detect_pi_model
    import subprocess
    
    try:
        # Determine Raspberry Pi model
        pi_model = detect_pi_model()
        
        # Read EEPROM settings for Pi 5
        eeprom_settings = {}
        power_manager = 'Unknown'
        
        if pi_model == '5':
            try:
                # Run rpi-eeprom-config command
                result = subprocess.run(['sudo', 'rpi-eeprom-config'], 
                                      capture_output=True, text=True)
                
                for line in result.stdout.split('\n'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        eeprom_settings[key] = value
                
                power_manager = 'Raspberry Pi EEPROM'
            except Exception as e:
                current_app.logger.error(f"Error reading EEPROM settings: {str(e)}")
        elif pi_model == '4':
            try:
                # Check if PiJuice is available
                from pijuice import PiJuice
                pj = PiJuice(1, 0x14)
                status = pj.status.GetStatus()
                if status['error'] == 'NO_ERROR':
                    power_manager = 'PiJuice'
            except ImportError:
                power_manager = 'Unknown'
            except Exception as e:
                current_app.logger.error(f"Error checking PiJuice: {str(e)}")
                power_manager = 'Unknown'
        
        return jsonify({
            'piModel': pi_model,
            'powerManager': power_manager,
            'POWER_OFF_ON_HALT': eeprom_settings.get('POWER_OFF_ON_HALT', '0'),
            'WAKE_ON_GPIO': eeprom_settings.get('WAKE_ON_GPIO', '0')
        })
    except Exception as e:
        current_app.logger.error(f"Error getting power settings: {str(e)}")
        return jsonify({
            'piModel': 'Unknown',
            'powerManager': 'Unknown',
            'POWER_OFF_ON_HALT': '0',
            'WAKE_ON_GPIO': '0'
        })

@system_bp.route('/power', methods=['POST'])
def update_power_settings():
    """Update power settings."""
    from ..utils.system import detect_pi_model
    import subprocess
    import json
    
    try:
        data = request.get_json()
        
        # Determine Raspberry Pi model
        pi_model = detect_pi_model()
        
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
            subprocess.run(['sudo', 'rpi-eeprom-config', '--apply', '/tmp/eeprom_config.txt'], 
                          check=True)
        
        return jsonify(create_success_response(message='Power settings updated'))
    except subprocess.CalledProcessError as e:
        current_app.logger.error(f"Error updating EEPROM settings: {str(e)}")
        raise APIError(
            ErrorCode.SYSTEM_COMMAND_FAILED,
            "Failed to update EEPROM settings",
            {"error": str(e)}
        )
    except Exception as e:
        current_app.logger.error(f"Error updating power settings: {str(e)}")
        raise APIError(
            ErrorCode.UNKNOWN_ERROR,
            "Failed to update power settings",
            {"error": str(e)}
        )
