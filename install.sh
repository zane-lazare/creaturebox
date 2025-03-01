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
    
    # Check for Python 3
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is required but not installed. Installing..."
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip
    fi
    
    # Check for pip
    if ! command -v pip3 &> /dev/null; then
        error "pip3 is required but not installed. Installing..."
        sudo apt-get update
        sudo apt-get install -y python3-pip
    fi
}

# Install required packages
install_packages() {
    log "Installing required packages..."
    
    # Update package lists
    sudo apt-get update
    
    # Install required packages
    sudo apt-get install -y \
        python3-picamera2 \
        python3-flask \
        python3-flask-cors \
        python3-opencv \
        python3-psutil \
        python3-schedule \
        python3-rpi.gpio \
        libcamera-apps \
        nginx
    
    # Install Python packages
    pip3 install --user RPi.GPIO schedule psutil pillow piexif
    
    log "Required packages installed successfully."
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
    
    # Copy software scripts from this repository
    if [ -d "$SCRIPT_DIR/src/Software" ] && [ "$(ls -A "$SCRIPT_DIR/src/Software" 2>/dev/null)" ]; then
        cp -r "$SCRIPT_DIR/src/Software/"* "$TARGET_DIR/Software/"
        log "Core software scripts copied successfully."
    else
        error "Software directory in repository is empty or missing. Please check the repository structure."
        exit 1
    fi
    
    # Copy configuration files from this repository
    if [ -d "$SCRIPT_DIR/src/config" ] && [ "$(ls -A "$SCRIPT_DIR/src/config" 2>/dev/null)" ]; then
        # Copy config files to target
        cp -r "$SCRIPT_DIR/src/config/"* "$TARGET_DIR/"
        log "Configuration files copied successfully."
    else
        error "Configuration directory in repository is empty or missing. Please check the repository structure."
        exit 1
    fi
    
    # Copy web files from this repository
    if [ -f "$SCRIPT_DIR/src/web/app.py" ]; then
        cp "$SCRIPT_DIR/src/web/app.py" "$TARGET_DIR/web/"
        log "Web application copied successfully."
    else
        error "Web application (app.py) not found in repository. Please check the repository structure."
        exit 1
    fi
    
    if [ -d "$SCRIPT_DIR/src/web/static" ] && [ "$(ls -A "$SCRIPT_DIR/src/web/static" 2>/dev/null)" ]; then
        cp -r "$SCRIPT_DIR/src/web/static/"* "$TARGET_DIR/web/static/"
        log "Web static files copied successfully."
    else
        error "Web static files directory is empty or missing. Please check the repository structure."
        exit 1
    fi
    
    # Copy README
    if [ -f "$SCRIPT_DIR/README.md" ]; then
        cp "$SCRIPT_DIR/README.md" "$TARGET_DIR/"
        log "README.md copied successfully."
    fi
    
    # Copy version and license
    if [ -f "$SCRIPT_DIR/LICENSE" ]; then
        cp "$SCRIPT_DIR/LICENSE" "$TARGET_DIR/"
        log "LICENSE copied successfully."
    fi
    
    log "All files copied successfully."
}

# Set file permissions
set_permissions() {
    log "Setting file permissions..."
    
    # Make scripts executable
    chmod +x "$TARGET_DIR/Software/"*.py 2>/dev/null || log "No Python scripts to make executable in Software directory"
    chmod +x "$TARGET_DIR/Software/"*.sh 2>/dev/null || log "No shell scripts to make executable in Software directory"
    chmod +x "$TARGET_DIR/web/app.py" 2>/dev/null || log "Could not make app.py executable"
    
    # Set permissions for directories
    chmod -R 755 "$TARGET_DIR/Software" 2>/dev/null || log "Could not set permissions for Software directory"
    chmod -R 755 "$TARGET_DIR/web" 2>/dev/null || log "Could not set permissions for web directory"
    chmod -R 755 "$TARGET_DIR/photos" 2>/dev/null || log "Could not set permissions for photos directory"
    chmod -R 755 "$TARGET_DIR/logs" 2>/dev/null || log "Could not set permissions for logs directory"
    
    # Set permissions for config files
    find "$TARGET_DIR" -name "*.csv" -exec chmod 644 {} \; 2>/dev/null || log "Could not set permissions for CSV files"
    [ -f "$TARGET_DIR/controls.txt" ] && chmod 644 "$TARGET_DIR/controls.txt" || log "Could not set permissions for controls.txt"
    
    log "File permissions set."
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

# Update paths in scripts
update_paths() {
    log "Updating paths in scripts..."
    
    # List of common paths to replace
    common_paths=(
        "/home/pi/Desktop/Mothbox"
        "/home/pi/Mothbox"
        "/home/creature/Mothbox"
        "/home/creature/Desktop/Mothbox"
        "/home/pi/CreatureBox"
        "/home/creature/CreatureBox"
        "~/CreatureBox"
        "~/Desktop/CreatureBox"
        "~/Desktop/Mothbox"
    )
    
    # Update paths in Python scripts
    log "Updating paths in Python scripts..."
    for script_file in $(find "$TARGET_DIR/Software" -name "*.py" -type f); do
        for old_path in "${common_paths[@]}"; do
            log "  Replacing '$old_path' with '$TARGET_DIR' in $(basename "$script_file")"
            sed -i "s|$old_path|$TARGET_DIR|g" "$script_file"
        done
    done
    
    # Update paths in shell scripts
    log "Updating paths in shell scripts..."
    for script_file in $(find "$TARGET_DIR/Software" -name "*.sh" -type f); do
        for old_path in "${common_paths[@]}"; do
            log "  Replacing '$old_path' with '$TARGET_DIR' in $(basename "$script_file")"
            sed -i "s|$old_path|$TARGET_DIR|g" "$script_file"
        done
    done
    
    # Update paths in web application
    if [ -f "$TARGET_DIR/web/app.py" ]; then
        log "Updating paths in web application..."
        for old_path in "${common_paths[@]}"; do
            log "  Replacing '$old_path' with '$TARGET_DIR' in app.py"
            sed -i "s|$old_path|$TARGET_DIR|g" "$TARGET_DIR/web/app.py"
        done
    fi
    
    # Update paths in any configuration files
    for config_file in "$TARGET_DIR"/*.csv "$TARGET_DIR/controls.txt"; do
        if [ -f "$config_file" ]; then
            log "Updating paths in $(basename "$config_file")..."
            for old_path in "${common_paths[@]}"; do
                sed -i "s|$old_path|$TARGET_DIR|g" "$config_file"
            done
        fi
    done
    
    log "All paths updated in scripts and configuration files."
}

# Set up web service
setup_web_service() {
    log "Setting up web service..."
    
    # Create service file
    cat > /tmp/creaturebox-web.service << EOL
[Unit]
Description=CreatureBox Web Interface
After=network.target

[Service]
User=$USER
WorkingDirectory=$TARGET_DIR/web
ExecStart=$(which python3) $TARGET_DIR/web/app.py
Restart=always
RestartSec=5
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=creaturebox-web

[Install]
WantedBy=multi-user.target
EOL
    
    # Install service file
    sudo mv /tmp/creaturebox-web.service /etc/systemd/system/
    
    # Configure Nginx as a reverse proxy
    cat > /tmp/creaturebox << EOL
server {
    listen 80;
    server_name creaturebox.local;

    location / {
        proxy_pass http://127.0.0.1:$WEB_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # For large uploads (photos, etc.)
    client_max_body_size 100M;
}
EOL
    
    # Install Nginx config
    sudo mv /tmp/creaturebox /etc/nginx/sites-available/
    sudo ln -sf /etc/nginx/sites-available/creaturebox /etc/nginx/sites-enabled/
    
    # Configure mDNS for easy access
    cat > /tmp/http.service << EOL
<?xml version="1.0" standalone='no'?>
<!DOCTYPE service-group SYSTEM "avahi-service.dtd">
<service-group>
 <name replace-wildcards="yes">CreatureBox Web Interface on %h</name>
 <service>
   <type>_http._tcp</type>
   <port>80</port>
   <txt-record>path=/</txt-record>
 </service>
</service-group>
EOL
    
    # Install mDNS config
    sudo mv /tmp/http.service /etc/avahi/services/
    
    # Add hostname to hosts file
    if ! grep -q "creaturebox.local" /etc/hosts; then
        echo "127.0.0.1   creaturebox.local" | sudo tee -a /etc/hosts > /dev/null
    fi
    
    # Reload services
    sudo systemctl daemon-reload
    sudo systemctl enable creaturebox-web.service
    sudo systemctl start creaturebox-web.service
    sudo systemctl restart nginx
    sudo systemctl restart avahi-daemon
    
    log "Web service set up successfully."
}

# Create example crontab entries
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

# Check repository structure
check_repository() {
    log "Checking repository structure..."
    
    # Define critical paths to check
    critical_paths=(
        "$SCRIPT_DIR/src/Software"
        "$SCRIPT_DIR/src/config"
        "$SCRIPT_DIR/src/web/app.py"
        "$SCRIPT_DIR/src/web/static"
    )
    
    # Check each path
    for path in "${critical_paths[@]}"; do
        if [ ! -e "$path" ]; then
            error "Repository is missing a critical component: $path"
            error "Please ensure you have downloaded the complete repository."
            exit 1
        fi
    done

    # Check for essential files
    essential_files=(
        "$SCRIPT_DIR/src/Software/TakePhoto.py"
        "$SCRIPT_DIR/src/Software/Scheduler.py"
        "$SCRIPT_DIR/src/config/camera_settings.csv"
        "$SCRIPT_DIR/src/config/schedule_settings.csv"
        "$SCRIPT_DIR/src/config/controls.txt"
    )
    
    # Check each file
    for file in "${essential_files[@]}"; do
        if [ ! -f "$file" ]; then
            error "Repository is missing an essential file: $file"
            error "Please ensure you have downloaded the complete repository."
            exit 1
        fi
    done
    
    log "Repository structure check passed."
}

# Main installation function
main() {
    log "Starting CreatureBox installation..."
    
    # Repository check
    check_repository
    
    # System checks and setup
    check_system
    install_packages
    create_directories
    
    # File operations
    copy_files
    set_permissions
    create_symlinks
    update_paths
    
    # Service setup
    setup_web_service
    create_crontab_example
    
    # Installation complete
    log "CreatureBox installation complete!"
    log "You can access the web interface at:"
    log "  http://creaturebox.local (from other devices on your network)"
    log "  http://localhost (from this device)"
    log
    log "If you cannot access using creaturebox.local, find your IP address with:"
    log "  hostname -I"
    log "And then access using: http://[YOUR_IP_ADDRESS]"
    log
    log "See $TARGET_DIR/README.md for usage instructions"
}

# Run main function
main
