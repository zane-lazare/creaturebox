# CreatureBox Installation Guide

This guide provides detailed instructions for installing and configuring CreatureBox on a Raspberry Pi device.

## System Requirements

- Raspberry Pi 4 or Pi 5 (recommended)
- Raspberry Pi OS Bullseye or newer
- Python 3.7 or newer
- At least 8GB microSD card
- Raspberry Pi Camera module or compatible camera
- Internet connection for initial setup

## Installation Options

### Option 1: Quick Installation (Recommended)

The quick installation method uses our installation script to set up everything automatically:

```bash
# Download the quick install script
wget https://raw.githubusercontent.com/zane-lazare/creaturebox/main/quick-install.sh

# Make it executable
chmod +x quick-install.sh

# Run the installer
./quick-install.sh
```

### Option 2: Manual Installation

If you prefer more control over the installation process:

```bash
# Clone the repository
git clone https://github.com/zane-lazare/creaturebox.git

# Go to the directory
cd creaturebox

# Run the installer
./install.sh
```

## Installation Process Details

The installation script performs the following actions:

1. Checks system requirements
2. Installs necessary system packages
3. Sets up a Python virtual environment at `~/creaturebox-venv`
4. Installs Python dependencies in the virtual environment
5. Creates the CreatureBox directory structure
6. Copies configuration files and scripts
7. Sets up the web interface service
8. Configures nginx as a web server
9. Verifies the installation

## Post-Installation

After installation completes, the CreatureBox web interface should be accessible at:

- From the Raspberry Pi itself: `http://localhost:5000`
- From other devices on your network: `http://creaturebox.local`
- Using the Pi's IP address: `http://[YOUR_PI_IP]:5000`

## Troubleshooting Installation Issues

If you encounter problems during installation:

1. Check the installation log:
   ```bash
   cat ~/CreatureBox/install.log
   ```

2. Run the verification script:
   ```bash
   source ~/creaturebox-venv/bin/activate
   python ~/CreatureBox/verify_installation.py
   ```

3. Check web service status:
   ```bash
   sudo systemctl status creaturebox-web.service
   ```

4. Check nginx configuration:
   ```bash
   sudo nginx -t
   ```

5. For more detailed troubleshooting, refer to the [Troubleshooting Guide](TROUBLESHOOTING.md).

## Virtual Environment Information

The CreatureBox installation uses a dedicated Python virtual environment to avoid conflicts with system Python packages. The virtual environment is located at `~/creaturebox-venv`.

### Activating the Virtual Environment

Before running CreatureBox scripts manually, you should activate the virtual environment:

```bash
source ~/creaturebox-venv/bin/activate
```

### Deactivating the Virtual Environment

When you're done, you can deactivate the virtual environment:

```bash
deactivate
```

## Manual Configuration

### Camera Settings

Camera settings can be modified in `~/CreatureBox/camera_settings.csv`:

| Setting | Description | Example Value |
|---------|-------------|---------------|
| LensPosition | Focus position in diopters | 6.0 |
| ExposureTime | Exposure time in microseconds | 500 |
| AnalogueGain | Gain value (1.0-16.0) | 1.5 |
| HDR | HDR photo mode (0=off, 3+=HDR with that many photos) | 3 |
| VerticalFlip | Flip image vertically (0=no, 1=yes) | 1 |

### Schedule Settings

Schedule when the system runs by editing `~/CreatureBox/schedule_settings.csv`:

| Setting | Description | Example Value |
|---------|-------------|---------------|
| minute | Minutes past the hour | 0 |
| hour | Hours of the day (semicolon separated) | 19;21;23;2;4 |
| weekday | Days of the week (1-7 for Mon-Sun) | 1;2;3;4;5;6;7 |
| runtime | Minutes to run before shutdown (0=no shutdown) | 60 |

## Next Steps

After installation, you should:

1. Configure your camera settings through the web interface
2. Set up a schedule for when the system should take photos
3. Test the system by taking a manual photo
4. Configure power management settings if needed

For detailed usage instructions, see the [User Guide](README.md).
