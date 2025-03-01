#!/bin/bash

# CreatureBox Installation Script
# -------------------------------
# This script installs the CreatureBox software and web dashboard

# Set strict error handling
set -e

# Variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${HOME}/CreatureBox"
LOG_FILE="${TARGET_DIR}/install.log"
WEB_PORT=5000

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running as root (which we don't want for the main installer)
if [ "$EUID" -eq 0 ]; then
    echo -e "${YELLOW}Warning: This script doesn't need to be run as root.${NC}"
    echo "The script will use sudo only when necessary."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Log function
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" >&2
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >> "$LOG_FILE"
}

# Check system requirements
check_system() {
    log "Checking system requirements..."
    
    # Check if running on Raspberry Pi
    if ! grep -q "Raspberry Pi" /proc/cpuinfo && ! grep -q "BCM" /proc/cpuinfo; then
        error "This script is designed to run on a Raspberry Pi."
        error "If you are running on a Pi but seeing this message, you can continue anyway."
        read -p "Continue installation? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Ensure system is up to date
    sudo apt-get update
    sudo apt-get upgrade -y
}

# Install required packages
install_packages() {
    log "Installing required packages..."
    
    # Update package lists and upgrade
    sudo apt-get update
    sudo apt-get upgrade -y
    
    # Install core system dependencies
    sudo apt-get install -y \
        git \
        wget \
        curl \
        software-properties-common \
        gnupg \
        ca-certificates
    
    # Install Python and related packages
    sudo apt-get install -y \
        python3 \
        python3-pip \
        python3-venv
    
    # Install camera dependencies
    sudo apt-get install -y \
        libcamera-dev \
        libcamera-apps \
        python3-libcamera \
        python3-picamera2
    
    # Install networking and wireless tools
    sudo apt-get install -y \
        network-manager \
        avahi-daemon \
        nginx \
        hostapd
    
    # Install additional system utilities
    sudo apt-get install -y \
        rsync \
        psmisc \
        vsftpd \
        samba
    
    # Install development and build tools
    sudo apt-get install -y \
        build-essential \
        cmake \
        pkg-config
    
    # Python package dependencies
    log "Installing Python dependencies via pip..."
    python3 -m pip install --user --upgrade pip setuptools wheel
    
    # Install Python packages
    python3 -m pip install --user \
        Flask \
        flask-cors \
        numpy \
        opencv-python-headless \
        Pillow \
        piexif \
        psutil \
        schedule \
        RPi.GPIO
    
    # Install optional dependencies
    python3 -m pip install --user \
        pandas \
        qrcode \
        matplotlib
    
    # PiJuice support (optional, for Pi 4)
    if lsusb | grep -q "PiJuice"; then
        log "PiJuice detected. Installing PiJuice packages..."
        sudo apt-get install -y \
            pijuice-base \
            pijuice-gui
    fi
    
    log "Package installation complete."
}

# Create directory structure
create_directories() {
    log "Creating directory structure at $TARGET_DIR..."
    
    mkdir -p "$TARGET_DIR"
    mkdir -p "$TARGET_DIR/Software"
    mkdir -p "$TARGET_DIR/photos"
    mkdir -p "$TARGET_DIR/photos_backedup"
    mkdir -p "$TARGET_DIR/logs"
    mkdir -p "$TARGET_DIR/web"
    mkdir -p "$TARGET_DIR/web/static"
    mkdir -p "$TARGET_DIR/web/static/css"
    mkdir -p "$TARGET_DIR/web/static/js"
    mkdir -p "$TARGET_DIR/web/static/img"
    
    log "Directory structure created."
}

# Copy files (similar to previous script)
copy_files() {
    log "Copying files to installation directory..."
    
    # Ensure source files exist
    if [ ! -d "$SCRIPT_DIR/src" ]; then
        error "Source directory not found. Ensure you're running the script from the repository root."
        exit 1
    fi
    
    # Copy files (same as previous script)
    cp -r "$SCRIPT_DIR/src/Software/"* "$TARGET_DIR/Software/"
    cp -r "$SCRIPT_DIR/src/config/"* "$TARGET_DIR/"
    cp "$SCRIPT_DIR/src/web/app.py" "$TARGET_DIR/web/"
    cp -r "$SCRIPT_DIR/src/web/static/"* "$TARGET_DIR/web/static/"
    
    # Copy README and LICENSE
    [ -f "$SCRIPT_DIR/README.md" ] && cp "$SCRIPT_DIR/README.md" "$TARGET_DIR/"
    [ -f "$SCRIPT_DIR/LICENSE" ] && cp "$SCRIPT_DIR/LICENSE" "$TARGET_DIR/"
    
    log "Files copied successfully."
}

# Set file permissions
set_permissions() {
    log "Setting file permissions..."
    
    # Make scripts executable
    find "$TARGET_DIR/Software" -type f \( -name "*.py" -o -name "*.sh" \) -exec chmod +x {} \;
    chmod +x "$TARGET_DIR/web/app.py"
    
    # Set directory permissions
    chmod -R 755 "$TARGET_DIR/Software"
    chmod -R 755 "$TARGET_DIR/web"
    chmod -R 755 "$TARGET_DIR/photos"
    chmod -R 755 "$TARGET_DIR/logs"
    
    # Set file permissions
    find "$TARGET_DIR" -type f -name "*.csv" -exec chmod 644 {} \;
    [ -f "$TARGET_DIR/controls.txt" ] && chmod 644 "$TARGET_DIR/controls.txt"
    
    log "Permissions set."
}

# Create symlinks
create_symlinks() {
    log "Creating symlinks for convenience..."
    
    # Create symlinks to main scripts
    for script in TakePhoto.py Scheduler.py Attract_On.py Attract_Off.py StopScheduledShutdown.py; do
        if [ -f "$TARGET_DIR/Software/$script" ]; then
            ln -sf "$TARGET_DIR/Software/$script" "$TARGET_DIR/$script"
            log "Created symlink for $script"
        else
            log "Could not create symlink for $script (file not found)"
        fi
    done
    
    log "Symlinks created."
}

# Set up web service
setup_web_service() {
    log "Setting up web service..."
    
    # Create systemd service file
    sudo tee /etc/systemd/system/creaturebox-web.service > /dev/null << EOL
[Unit]
Description=CreatureBox Web Interface
After=network.target

[Service]
User=$USER
WorkingDirectory=$TARGET_DIR/web
ExecStart=$(which python3) $TARGET_DIR/web/app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOL
    
    # Configure Nginx
    sudo tee /etc/nginx/sites-available/creaturebox > /dev/null << EOL
server {
    listen 80;
    server_name creaturebox.local;

    location / {
        proxy_pass http://127.0.0.1:$WEB_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }

    client_max_body_size 100M;
}
EOL
    
    # Enable sites and restart services
    sudo ln -sf /etc/nginx/sites-available/creaturebox /etc/nginx/sites-enabled/
    sudo systemctl enable creaturebox-web.service
    sudo systemctl start creaturebox-web.service
    sudo systemctl restart nginx
    
    log "Web service set up successfully."
}

# Create crontab example file
create_crontab_example() {
    log "Creating crontab example file..."
    
    cat > "$TARGET_DIR/crontab.example" << EOL
# Example crontab entries for CreatureBox
# To install: crontab -e

# Take photo every hour
0 * * * * python3 ${TARGET_DIR}/TakePhoto.py

# Run scheduler at boot
@reboot python3 ${TARGET_DIR}/Scheduler.py

# Backup photos daily at 3 AM
0 3 * * * python3 ${TARGET_DIR}/Software/Backup_Files.py
EOL
    
    log "Crontab example file created at $TARGET_DIR/crontab.example"
}

# Main installation function
main() {
    log "Starting CreatureBox installation..."
    
    # System checks and setup
    check_system
    install_packages
    create_directories
    
    # File operations
    copy_files
    set_permissions
    create_symlinks
    
    # Service setup
    setup_web_service
    create_crontab_example
    
    # Installation complete
    log "CreatureBox installation complete!"
    log "You can access the web interface at:"
    log "  http://creaturebox.local (from other devices on your network)"
    log "  http://localhost (from this device)"
    log
    log "Find your IP address with: hostname -I"
    log
    log "See $TARGET_DIR/README.md for usage instructions"
}

# Run main function
main
