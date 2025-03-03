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
echo "CreatureBox Installer - Wildlife Monitoring System"
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

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d ' ' -f 2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

echo "Detected Python version: $PYTHON_VERSION"

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 7 ]); then
    echo -e "${RED}Error: CreatureBox requires Python 3.7 or newer.${NC}"
    echo "Please upgrade your Python installation before continuing."
    exit 1
fi

# Check if necessary packages are installed
echo "Checking for required packages..."

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo -e "${YELLOW}Git is not installed. Installing...${NC}"
    sudo apt-get update
    sudo apt-get install -y git
fi

# Check if python3-venv is installed
if ! dpkg -l | grep -q python3-venv; then
    echo -e "${YELLOW}python3-venv is not installed. Installing...${NC}"
    sudo apt-get update
    sudo apt-get install -y python3-venv
fi

# Set temporary installation directory
TEMP_DIR="/tmp/creaturebox-install"
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"

# Ask for custom installation directory or use default
read -p "Enter installation directory (default: ~/CreatureBox): " INSTALL_DIR
INSTALL_DIR=${INSTALL_DIR:-"$HOME/CreatureBox"}

# Ask for virtual environment location or use default
read -p "Enter Python virtual environment location (default: ~/creaturebox-venv): " VENV_PATH
VENV_PATH=${VENV_PATH:-"$HOME/creaturebox-venv"}

echo -e "${GREEN}Will install to: $INSTALL_DIR${NC}"
echo -e "${GREEN}Will use virtual environment at: $VENV_PATH${NC}"
echo

#
