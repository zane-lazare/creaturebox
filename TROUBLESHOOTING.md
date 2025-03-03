# CreatureBox Troubleshooting Guide

This guide provides solutions to common issues you might encounter when setting up or using CreatureBox.

## Installation Issues

### Python Dependencies Installation Fails

**Symptoms:**
- Error messages about "externally managed environment"
- Missing Python modules after installation

**Solutions:**
1. Make sure the virtual environment is properly activated:
   ```bash
   source ~/creaturebox-venv/bin/activate
   ```

2. Try reinstalling the requirements manually:
   ```bash
   pip install -r ~/CreatureBox/requirements.txt
   ```

3. Check Python version compatibility:
   ```bash
   python --version
   ```
   CreatureBox requires Python 3.7 or newer.

### Web Service Doesn't Start

**Symptoms:**
- Cannot access the web interface
- Error messages in service logs

**Solutions:**
1. Check the service status:
   ```bash
   sudo systemctl status creaturebox-web.service
   ```

2. View the service logs for errors:
   ```bash
   sudo journalctl -u creaturebox-web.service
   ```

3. Make sure the virtual environment path is correct in the service definition:
   ```bash
   sudo nano /etc/systemd/system/creaturebox-web.service
   ```
   Verify that `ExecStart` points to the correct Python path.

4. Restart the service after making changes:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart creaturebox-web.service
   ```

## Camera Issues

### Camera Not Working

**Symptoms:**
- No photos are captured
- Error messages about camera access

**Solutions:**
1. Make sure the camera is enabled:
   ```bash
   sudo raspi-config
   ```
   Navigate to "Interface Options" > "Camera" and enable it.

2. Check camera connections:
   - For Pi Camera Module: Make sure the ribbon cable is properly connected
   - For USB cameras: Run `lsusb` to verify the camera is detected

3. Test basic camera functionality:
   ```bash
   libcamera-still -o test.jpg
   ```

4. For Arducam 64MP cameras, check specific drivers are installed:
   ```bash
   ~/CreatureBox/Software/Scripts/CheckCameraDrivers.py
   ```

### Photos are Too Dark or Blurry

**Symptoms:**
- Captured images are too dark, over-exposed, or out of focus

**Solutions:**
1. Update camera settings in camera_settings.csv:
   ```bash
   nano ~/CreatureBox/camera_settings.csv
   ```
   - Increase `ExposureTime` for brighter images
   - Adjust `LensPosition` for focus
   - Modify `AnalogueGain` for sensitivity

2. Run calibration:
   ```bash
   ~/CreatureBox/TakePhoto.py --calibrate
   ```

3. For lighting issues, check that flash/lights are operating correctly:
   ```bash
   ~/CreatureBox/Attract_On.py
   ```

## Scheduling Issues

### System Doesn't Wake Up on Schedule

**Symptoms:**
- No activity at scheduled times
- No new photos taken

**Solutions:**
1. Check schedule settings:
   ```bash
   nano ~/CreatureBox/schedule_settings.csv
   ```

2. Make sure the RTC (Real Time Clock) is working:
   ```bash
   sudo hwclock -r
   ```

3. For Pi 5, ensure EEPROM settings are correct:
   ```bash
   sudo rpi-eeprom-config
   ```
   Look for `WAKE_ON_GPIO=0` and `POWER_OFF_ON_HALT=1`

4. For Pi 4 with PiJuice, check PiJuice status:
   ```bash
   pijuice_cli status
   ```

5. Manually run the scheduler to verify it works:
   ```bash
   ~/creaturebox-venv/bin/python ~/CreatureBox/Scheduler.py
   ```

### System Doesn't Shut Down on Schedule

**Symptoms:**
- System stays on indefinitely
- Battery drains quickly

**Solutions:**
1. Check runtime setting in schedule_settings.csv:
   ```bash
   nano ~/CreatureBox/schedule_settings.csv
   ```
   Make sure `runtime` is set to a value greater than 0.

2. Check shutdown_enabled flag in controls.txt:
   ```bash
   nano ~/CreatureBox/controls.txt
   ```
   Make sure `shutdown_enabled=True`

3. For Pi 4 with PiJuice, ensure the PiJuice firmware is up to date:
   ```bash
   pijuice_cli fw
   ```

## Network and Web Interface Issues

### Cannot Access Web Interface

**Symptoms:**
- Unable to connect to the web interface
- Browser returns connection error

**Solutions:**
1. Check the web service is running:
   ```bash
   sudo systemctl status creaturebox-web.service
   ```

2. Check network connectivity and find the IP address:
   ```bash
   hostname -I
   ```

3. Ensure Nginx is properly configured and running:
   ```bash
   sudo systemctl status nginx
   sudo nginx -t
   ```

4. Try accessing directly via IP and port:
   ```
   http://[YOUR_PI_IP]:5000
   ```

5. Restart the web services:
   ```bash
   sudo systemctl restart creaturebox-web.service
   sudo systemctl restart nginx
   ```

### WiFi Connectivity Issues

**Symptoms:**
- System can't connect to WiFi
- Intermittent network connectivity

**Solutions:**
1. Check current WiFi status:
   ```bash
   nmcli dev wifi
   ```

2. Connect to a specific network:
   ```bash
   nmcli dev wifi connect "SSID" password "password"
   ```

3. For adding networks via the web interface, check the settings.csv file:
   ```bash
   nano ~/CreatureBox/schedule_settings.csv
   ```

## Data and Storage Issues

### Photos Not Being Saved

**Symptoms:**
- Camera works but no photos in the photos directory
- Error messages about write permissions

**Solutions:**
1. Check directory permissions:
   ```bash
   ls -la ~/CreatureBox/photos
   ```

2. Ensure there's enough storage space:
   ```bash
   df -h
   ```

3. Try capturing a photo manually:
   ```bash
   ~/creaturebox-venv/bin/python ~/CreatureBox/TakePhoto.py
   ```

### Photos Not Being Backed Up

**Symptoms:**
- External drive connected but files aren't copied

**Solutions:**
1. Check if external drive is mounted:
   ```bash
   df -h
   ```

2. Try running backup manually:
   ```bash
   ~/creaturebox-venv/bin/python ~/CreatureBox/Software/Backup_Files.py
   ```

3. Check backup script logs:
   ```bash
   cat ~/CreatureBox/logs/backup.log
   ```

## Advanced Troubleshooting

### Completely Reset Installation

If you need to start fresh:

1. Stop services:
   ```bash
   sudo systemctl stop creaturebox-web.service
   ```

2. Remove the virtual environment:
   ```bash
   rm -rf ~/creaturebox-venv
   ```

3. Remove the CreatureBox directory (caution - this deletes all your data):
   ```bash
   rm -rf ~/CreatureBox
   ```

4. Clean up system services:
   ```bash
   sudo rm /etc/systemd/system/creaturebox-web.service
   sudo rm /etc/nginx/sites-enabled/creaturebox
   sudo systemctl daemon-reload
   ```

5. Reinstall following the standard installation process.

### Logs Analysis

Logs can provide valuable debug information:

1. Installation logs:
   ```bash
   cat ~/CreatureBox/install.log
   ```

2. Web service logs:
   ```bash
   sudo journalctl -u creaturebox-web.service
   ```

3. System logs related to camera:
   ```bash
   dmesg | grep -i camera
   ```

4. Custom CreatureBox logs:
   ```bash
   ls -la ~/CreatureBox/logs/
   ```

## Getting Help

If you're still experiencing issues:

1. Check the GitHub repository for known issues and their solutions
2. Gather your logs and system information for reporting:
   ```bash
   ~/CreatureBox/Software/Scripts/GatherDebugInfo.py
   ```
3. Open an issue on the GitHub repository with the debug information
