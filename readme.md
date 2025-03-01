# CreatureBox

![CreatureBox Logo](src/web/static/img/creaturebox-logo.png)

A fork of the Mothbox insect monitoring system, enhanced with a web dashboard interface for easy headless management of wildlife cameras.

## Overview

CreatureBox is an automated wildlife camera system based on the original Mothbox, designed to capture images of animals on a scheduled basis. It uses a Raspberry Pi with a camera module, attraction lights, and a web-based dashboard for easy monitoring and control.

## Features

- **Automated Photo Capture**: Schedule when the system should capture photos
- **Web Dashboard**: Control your device from any browser on your network
- **Camera Controls**: Adjust settings, calibrate, and capture manually
- **Photo Gallery**: Browse, view, and manage your captured images
- **System Monitoring**: View device status, storage, and power information
- **Mobile Friendly**: Interface works on smartphones and tablets

## Quick Installation

### One-Command Installation

```bash
# Download the quick install script
wget https://raw.githubusercontent.com/zane-lazare/creaturebox/main/quick-install.sh
# Make it executable
chmod +x quick-install.sh
# Run the installer
./quick-install.sh
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/zane-lazare/creaturebox.git
# Go to the directory
cd creaturebox
# Run the installer
./install.sh
```

## Accessing the Web Dashboard

After installation, you can access the CreatureBox web dashboard using:

- From the Raspberry Pi itself: `http://localhost`
- From other devices on your network: `http://creaturebox.local`
- Using the Pi's IP address: `http://[YOUR_PI_IP_ADDRESS]`

If you cannot access the dashboard using `creaturebox.local`, find your Pi's IP address by running:

```bash
hostname -I
```

## Hardware Setup

### Required Components

- Raspberry Pi (Pi 4 or Pi 5 recommended)
- Raspberry Pi Camera Module
- UV/attraction lights (optional)
- Power supply
- MicroSD card (16GB or larger recommended)

### Wiring Diagram

The relay control uses the following GPIO pins:

- Relay_Ch1 (Pin 26): Main attraction lights
- Relay_Ch2 (Pin 20): Flash control
- Relay_Ch3 (Pin 21): Secondary attraction lights

## Software Components

The CreatureBox system consists of several key components:

- **TakePhoto.py**: Main script for capturing photos
- **Scheduler.py**: Manages the schedule for when photos should be taken
- **Web Dashboard**: Browser-based control interface
- **Configuration Files**: Settings for camera, schedule, and system control

## Configuration

### Camera Settings

Edit `~/CreatureBox/camera_settings.csv` to configure camera parameters:

| Setting | Description | Example Value |
|---------|-------------|---------------|
| LensPosition | Focus position in diopters | 6.0 |
| ExposureTime | Exposure time in microseconds | 500 |
| AnalogueGain | Gain value (1.0-16.0) | 1.5 |
| HDR | HDR photo mode (0=off, 3+=HDR with that many photos) | 3 |
| VerticalFlip | Flip image vertically (0=no, 1=yes) | 1 |

### Schedule Settings

Edit `~/CreatureBox/schedule_settings.csv` to configure when the system runs:

| Setting | Description | Example Value |
|---------|-------------|---------------|
| minute | Minutes past the hour | 0 |
| hour | Hours of the day (semicolon separated) | 19;21;23;2;4 |
| weekday | Days of the week (1-7 for Mon-Sun) | 1;2;3;4;5;6;7 |
| runtime | Minutes to run before shutdown (0=no shutdown) | 60 |

## Usage

### Dashboard

The web dashboard provides an intuitive interface for controlling your CreatureBox:

1. **Dashboard Tab**: View system status, storage usage, power information
2. **Camera Tab**: Adjust camera settings, take photos, calibrate
3. **Settings Tab**: Configure schedule, WiFi, and other settings
4. **Gallery Tab**: Browse and manage photos
5. **Logs Tab**: View system logs for troubleshooting

### Manual Photo Capture

To manually take a photo:

```bash
cd ~/CreatureBox
python3 TakePhoto.py
```

### Scheduling

To set up the automatic schedule:

```bash
cd ~/CreatureBox
python3 Scheduler.py
```

This will read the settings from `schedule_settings.csv` and set up the system to take photos at the specified times.

### Debugging Mode

To put the system in debug mode (keeping power and WiFi on):

```bash
cd ~/CreatureBox
python3 Software/DebugMode.py
```

## Troubleshooting

### Web Dashboard Issues

If you can't access the web dashboard:

1. Check if the service is running:
   ```bash
   sudo systemctl status creaturebox-web.service
   ```

2. Restart the service if needed:
   ```bash
   sudo systemctl restart creaturebox-web.service
   ```

3. Check service logs:
   ```bash
   sudo journalctl -u creaturebox-web.service
   ```

### Camera Issues

If the camera isn't working:

1. Check if the camera is enabled in Raspberry Pi configuration:
   ```bash
   sudo raspi-config
   ```
   Navigate to "Interface Options" > "Camera" and enable it.

2. Make sure the camera is properly connected to the Raspberry Pi.

3. Manually test the camera:
   ```bash
   libcamera-still -o test.jpg
   ```

### Photo Storage Issues

If photos aren't being saved:

1. Check the permissions on the photos directory:
   ```bash
   ls -la ~/CreatureBox/photos
   ```

2. Make sure the directory exists and is writable:
   ```bash
   mkdir -p ~/CreatureBox/photos
   chmod 755 ~/CreatureBox/photos
   ```

### Schedule Issues

If scheduling isn't working:

1. Check the RTC (Real Time Clock) settings:
   ```bash
   sudo hwclock -r
   ```

2. Manually run the scheduler:
   ```bash
   python3 ~/CreatureBox/Scheduler.py
   ```

## Customization

### Changing Port

To change the web interface port (default is 5000):

1. Edit the web application:
   ```bash
   nano ~/CreatureBox/web/app.py
   ```
   Change the line `app.run(host='0.0.0.0', port=5000, threaded=True)`

2. Update the Nginx configuration:
   ```bash
   sudo nano /etc/nginx/sites-available/creaturebox
   ```
   Update the `proxy_pass` line to match the new port.

3. Restart services:
   ```bash
   sudo systemctl restart creaturebox-web.service
   sudo systemctl restart nginx
   ```

### Adding Authentication

To add basic authentication to the web interface:

1. Install the necessary tools:
   ```bash
   sudo apt-get install apache2-utils
   ```

2. Create password file:
   ```bash
   sudo htpasswd -c /etc/nginx/.htpasswd admin
   ```
   Follow the prompts to set a password.

3. Edit Nginx configuration:
   ```bash
   sudo nano /etc/nginx/sites-available/creaturebox
   ```
   Add the following inside the `server` block:
   ```
   auth_basic "Restricted";
   auth_basic_user_file /etc/nginx/.htpasswd;
   ```

4. Restart Nginx:
   ```bash
   sudo systemctl restart nginx
   ```

## Updating

To update CreatureBox:

1. Go to your repository directory:
   ```bash
   cd ~/creaturebox
   ```

2. Pull the latest changes:
   ```bash
   git pull
   ```

3. Run the installer:
   ```bash
   ./install.sh
   ```

## Directory Structure

```
~/CreatureBox/
├── Software/          # Main Python scripts
├── photos/            # Captured photos
├── photos_backedup/   # Backed up photos
├── logs/              # Log files
├── web/               # Web interface files
├── camera_settings.csv
├── schedule_settings.csv
├── controls.txt
└── *.py               # Symlinks to main scripts
```

## Contributing

Contributions to CreatureBox are welcome! Please feel free to submit pull requests or create issues for bugs and feature requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Original Mothbox v4.1 created by Digital Naturalism Laboratories
- Based on the work at [https://github.com/digitalnaturam/mothbox](https://github.com/digitalnaturam/mothbox)
