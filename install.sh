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
VENV_PATH="${HOME}/creaturebox-venv"

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
    
    # Check Python version
    python_version=$(python3 --version 2>&1 | cut -d ' ' -f 2)
    log "Detected Python version: $python_version"
    python_major=$(echo $python_version | cut -d. -f1)
    python_minor=$(echo $python_version | cut -d. -f2)
    
    if [ "$python_major" -lt 3 ] || ([ "$python_major" -eq 3 ] && [ "$python_minor" -lt 7 ]); then
        error "CreatureBox requires Python 3.7+. Please upgrade your Python installation."
        exit 1
    fi
    
    # Ensure system is up to date
    log "Updating package lists..."
    sudo apt-get update
}

# Install required system packages
install_packages() {
    log "Installing required system packages..."
    
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
        nginx
    
    # Install additional system utilities
    sudo apt-get install -y \
        rsync \
        psmisc
    
    log "System package installation complete."
}

# Setup Python virtual environment
setup_venv() {
    log "Setting up Python virtual environment..."
    
    # Ensure Python3 venv is available
    if ! dpkg -l | grep -q python3-venv; then
        log "Installing python3-venv..."
        sudo apt-get update
        sudo apt-get install -y python3-venv
    fi
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "$VENV_PATH" ]; then
        log "Creating virtual environment at $VENV_PATH..."
        python3 -m venv "$VENV_PATH"
    else
        log "Virtual environment already exists at $VENV_PATH"
    fi
    
    # Activate virtual environment
    log "Activating virtual environment..."
    source "$VENV_PATH/bin/activate"
    
    # Upgrade pip within the virtual environment
    log "Upgrading pip, setuptools, and wheel..."
    pip install --upgrade pip setuptools wheel
    
    log "Python virtual environment setup complete."
}

# Install Python dependencies
install_python_deps() {
    log "Installing Python dependencies..."
    
    # Make sure virtual environment is activated
    if [[ "$VIRTUAL_ENV" != "$VENV_PATH" ]]; then
        source "$VENV_PATH/bin/activate"
    fi
    
    # Check if requirements.txt exists
    if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
        log "Installing from requirements.txt..."
        pip install -r "$SCRIPT_DIR/requirements.txt"
    else
        # Fallback to inline installation if requirements.txt isn't found
        log "requirements.txt not found, installing packages directly..."
        pip install \
            Flask==2.1.0 \
            flask-cors==3.0.10 \
            numpy==1.22.0 \
            opencv-python-headless==4.5.5.64 \
            Pillow==9.0.0 \
            piexif==1.1.3 \
            psutil==5.9.0 \
            RPi.GPIO==0.7.0 \
            schedule==1.1.0 \
            python-crontab==2.6.0
    fi
    
    # Check if PiJuice is present and install the module if needed
    if lsusb | grep -q "PiJuice"; then
        log "PiJuice detected, installing PiJuice Python module..."
        pip install pijuice.py
    fi
    
    log "Python dependencies installed successfully."
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

# Copy files
copy_files() {
    log "Copying files to installation directory..."
    
    # Ensure source files exist
    if [ ! -d "$SCRIPT_DIR/src" ]; then
        error "Source directory not found. Ensure you're running the script from the repository root."
        exit 1
    fi
    
    # Copy files
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
ExecStart=$VENV_PATH/bin/python $TARGET_DIR/web/app.py
Restart=always
RestartSec=5
Environment="PATH=$VENV_PATH/bin:$PATH"

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
0 * * * * $VENV_PATH/bin/python ${TARGET_DIR}/TakePhoto.py

# Run scheduler at boot
@reboot $VENV_PATH/bin/python ${TARGET_DIR}/Scheduler.py

# Backup photos daily at 3 AM
0 3 * * * $VENV_PATH/bin/python ${TARGET_DIR}/Software/Backup_Files.py
EOL
    
    log "Crontab example file created at $TARGET_DIR/crontab.example"
}

# Verify installation
verify_installation() {
    log "Verifying installation..."
    
    # Check if critical files exist
    local missing_files=0
    for file in "$TARGET_DIR/TakePhoto.py" "$TARGET_DIR/Scheduler.py" "$TARGET_DIR/web/app.py"; do
        if [ ! -f "$file" ]; then
            error "Missing critical file: $file"
            missing_files=$((missing_files + 1))
        fi
    done
    
    # Check if web service is running
    if ! systemctl is-active --quiet creaturebox-web.service; then
        error "Web service is not running. Check logs with: sudo journalctl -u creaturebox-web.service"
        missing_files=$((missing_files + 1))
    fi
    
    # Check Python dependencies in virtual environment
    local missing_deps=0
    for dep in flask numpy opencv-python-headless pillow; do
        if ! $VENV_PATH/bin/pip list | grep -i "$dep" > /dev/null; then
            error "Missing Python dependency: $dep"
            missing_deps=$((missing_deps + 1))
        fi
    done
    
    if [ $missing_files -eq 0 ] && [ $missing_deps -eq 0 ]; then
        log "Installation verification successful!"
        return 0
    else
        error "Installation verification failed with $missing_files missing files and $missing_deps missing dependencies."
        error "Please check the log file at $LOG_FILE for details."
        return 1
    fi
}

# Main installation function
main() {
    log "Starting CreatureBox installation..."
    
    # System checks and setup
    check_system
    install_packages
    
    # Python environment setup
    setup_venv
    
    # Trap to deactivate virtual environment on script exit
    trap 'deactivate' EXIT
    
    # Python dependencies
    install_python_deps
    
    # Directory structure and files
    create_directories
    copy_files
    set_permissions
    create_symlinks
    
    # Service setup
    setup_web_service
    create_crontab_example
    
    # Verify installation
    verify_installation
    
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
