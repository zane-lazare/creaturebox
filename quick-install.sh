#!/bin/bash

# CreatureBox Quick Installer
# --------------------------
# This script pulls the CreatureBox repository from GitHub and runs the installer

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print banner
echo -e "${GREEN}"
echo "  ____                _                  ____            "
echo " / ___|_ __ ___  __ _| |_ _   _ _ __ ___| __ )  _____  __"
echo "| |   | '__/ _ \/ _\` | __| | | | '__/ _ \  _ \ / _ \ \/ /"
echo "| |___| | |  __/ (_| | |_| |_| | | |  __/ |_) | (_) >  < "
echo " \____|_|  \___|\__,_|\__|\__,_|_|  \___|____/ \___/_/\_\\"
echo -e "${NC}"
echo "CreatureBox Installer - Animal Monitoring System"
echo "----------------------------------------------"
echo "This script will install CreatureBox on your system."
echo

# Check if running on a Raspberry Pi
if ! grep -q "Raspberry Pi\|BCM" /proc/cpuinfo 2>/dev/null; then
    echo -e "${YELLOW}Warning: This script is designed to run on a Raspberry Pi.${NC}"
    echo "If you are on a Pi but seeing this message, you can continue anyway."
    read -p "Continue installation? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo -e "${YELLOW}Git is not installed. Installing...${NC}"
    sudo apt-get update
    sudo apt-get install -y git
fi

# Set temporary installation directory
TEMP_DIR="/tmp/creaturebox-install"
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"

# Ask for custom installation directory or use default
read -p "Enter installation directory (default: ~/CreatureBox): " INSTALL_DIR
INSTALL_DIR=${INSTALL_DIR:-"$HOME/CreatureBox"}

echo -e "${GREEN}Will install to: $INSTALL_DIR${NC}"
echo

# Clone the repository
echo "Cloning CreatureBox repository..."
git clone https://github.com/zane-lazare/creaturebox.git "$TEMP_DIR"

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to clone repository. Please check your internet connection and try again.${NC}"
    exit 1
fi

# Check if repository has the expected structure
echo "Checking repository structure..."
essential_dirs=(
    "$TEMP_DIR/src/Software"
    "$TEMP_DIR/src/config"
    "$TEMP_DIR/src/web"
)

essential_files=(
    "$TEMP_DIR/install.sh"
    "$TEMP_DIR/src/web/app.py"
    "$TEMP_DIR/src/config/camera_settings.csv"
    "$TEMP_DIR/src/config/schedule_settings.csv"
)

# Check directories
for dir in "${essential_dirs[@]}"; do
    if [ ! -d "$dir" ]; then
        echo -e "${RED}Error: Missing essential directory: $dir${NC}"
        echo "The repository might be incomplete. Please try again or clone it manually."
        exit 1
    fi
done

# Check files
for file in "${essential_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}Error: Missing essential file: $file${NC}"
        echo "The repository might be incomplete. Please try again or clone it manually."
        exit 1
    fi
done

echo -e "${GREEN}Repository structure looks good!${NC}"

# Make the installer executable
chmod +x "$TEMP_DIR/install.sh"

# Run the installer
echo "Running installer..."
"$TEMP_DIR/install.sh"

# Cleanup
rm -rf "$TEMP_DIR"

echo
echo -e "${GREEN}CreatureBox installation complete!${NC}"
echo "You can access the web interface at:"
echo "  http://creaturebox.local   (from other devices on the network)"
echo "  http://localhost           (from the Raspberry Pi itself)"
echo
echo "To find your IP address, run: hostname -I"
echo
echo "For more information, see the README.md file in your installation directory."
