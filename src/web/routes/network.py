# src/web/routes/network.py
from flask import Blueprint, jsonify, request, current_app
import subprocess
from ..error_handlers import APIError, ErrorCode
from .api import create_success_response

# Create blueprint
network_bp = Blueprint('network', __name__, url_prefix='/api/network')

@network_bp.route('/status')
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
        current_app.logger.error(f"Error getting network status: {str(e)}")
        return jsonify({
            'connected': False,
            'ssid': None,
            'ip': 'Not available',
            'signalStrength': 0
        })

@network_bp.route('/add', methods=['POST'])
def add_network():
    """Add a new WiFi network."""
    data = request.get_json()
    
    if 'ssid' not in data or 'wifipass' not in data:
        raise APIError(
            ErrorCode.INVALID_REQUEST,
            "SSID and password required"
        )
    
    # Update schedule settings file with new WiFi credentials
    from ..utils.files import write_csv_settings
    from ..config import SCHEDULE_SETTINGS_FILE
    
    settings = {
        'ssid': data['ssid'],
        'wifipass': data['wifipass']
    }
    
    success = write_csv_settings(SCHEDULE_SETTINGS_FILE, settings)
    
    if success:
        # Run RegisterNewWifi.sh script
        try:
            subprocess.Popen(['sudo', 'RegisterNewWifi.sh'])
            return jsonify(create_success_response(message='WiFi network added successfully'))
        except Exception as e:
            current_app.logger.error(f"Error running WiFi registration script: {str(e)}")
            raise APIError(
                ErrorCode.SYSTEM_COMMAND_FAILED,
                "Failed to register WiFi network",
                {"error": str(e)}
            )
    else:
        raise APIError(
            ErrorCode.UNKNOWN_ERROR,
            "Failed to add network settings"
        )
