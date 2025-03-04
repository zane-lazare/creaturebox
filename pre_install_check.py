#!/usr/bin/env python3
"""
CreatureBox Pre-Installation Check Script
----------------------------------------
This script checks if the system meets the requirements for installing CreatureBox.
"""

import os
import sys
import platform
import subprocess
import shutil
import re

# ANSI color codes
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
NC = '\033[0m'  # No Color

def print_banner():
    """Print the CreatureBox banner."""
    print(f"{GREEN}")
    print("  ____                _                  ____            ")
    print(" / ___|_ __ ___  __ _| |_ _   _ _ __ ___| __ )  _____  __")
    print("| |   | '__/ _ \/ _` | __| | | | '__/ _ \  _ \ / _ \ \/ /")
    print("| |___| | |  __/ (_| | |_| |_| | | |  __/ |_) | (_) >  < ")
    print(" \____|_|  \___|\__,_|\__|\__,_|_|  \___|____/ \___/_/\_\\")
    print(f"{NC}")
    print("CreatureBox Pre-Installation Check")
    print("----------------------------------")
    print()

def check_python_version():
    """Check if Python version is 3.7 or newer."""
    print("Checking Python version...")
    
    python_version = platform.python_version()
    python_version_tuple = tuple(map(int, python_version.split('.')))
    
    if python_version_tuple >= (3, 7):
        print(f"{GREEN}✓ Python version {python_version} detected (3.7+ required).{NC}")
        return True
    else:
        print(f"{RED}✗ Python version {python_version} is not supported.{NC}")
        print(f"{RED}  CreatureBox requires Python 3.7 or newer.{NC}")
        return False

def check_raspberry_pi():
    """Check if running on a Raspberry Pi."""
    print("Checking system architecture...")
    
    # Check for Raspberry Pi model in /proc/cpuinfo
    try:
        is_raspberry_pi = False
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            is_raspberry_pi = 'Raspberry Pi' in cpuinfo or 'BCM' in cpuinfo
        
        if is_raspberry_pi:
            # Try to get the model
            model_match = re.search(r'Model\s+:\s+(.+)', cpuinfo)
            if model_match:
                model = model_match.group(1)
                print(f"{GREEN}✓ Raspberry Pi detected: {model}{NC}")
            else:
                print(f"{GREEN}✓ Raspberry Pi detected.{NC}")
            return True
        else:
            print(f"{YELLOW}! Not running on a Raspberry Pi.{NC}")
            print(f"{YELLOW}  This software is designed for Raspberry Pi hardware.{NC}")
            return False
    except Exception as e:
        print(f"{YELLOW}! Could not determine if this is a Raspberry Pi: {e}{NC}")
        return False



def check_disk_space():
    """Check if there's enough disk space."""
    print("Checking available disk space...")
    
    # Check available space in the home directory
    home_dir = os.path.expanduser('~')
    try:
        stat = os.statvfs(home_dir)
        available_space_mb = (stat.f_bavail * stat.f_frsize) / (1024 * 1024)
        
        if available_space_mb >= 1000:  # At least 1 GB
            print(f"{GREEN}✓ Available space: {available_space_mb:.2f} MB (minimum 1000 MB required).{NC}")
            return True
        else:
            print(f"{RED}✗ Low disk space: {available_space_mb:.2f} MB available.{NC}")
            print(f"{RED}  At least 1000 MB (1 GB) is recommended.{NC}")
            return False
    except Exception as e:
        print(f"{YELLOW}! Could not check disk space: {e}{NC}")
        return False
        
def check_camera():
    """Check if a camera is available."""
    print("Checking camera availability...")    
    # Try using libcamera-hello --list-cameras (more reliable with picamera2)
    try:
        result = subprocess.run(['libcamera-hello', '--list-cameras'], 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                               text=True, check=False)        
        if "Available cameras" in result.stdout and not "No cameras available" in result.stdout:
            print(f"{GREEN}✓ Camera detected using libcamera-hello.{NC}")
            return True
    except Exception as e:
        pass    
    # Original detection methods
    try:
        result = subprocess.run(['vcgencmd', 'get_camera'], 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                               text=True, check=False)        
        if 'detected=1' in result.stdout:
            print(f"{GREEN}✓ Camera module is detected and enabled.{NC}")
            return True
        else:
            print(f"{YELLOW}! Camera module is not detected or not enabled.{NC}")
            print(f"{YELLOW}  You may need to enable it using 'sudo raspi-config'.{NC}")
    except:
        pass        
    # Try an alternative approach
    if os.path.exists('/dev/video0'):
        print(f"{GREEN}✓ Camera device /dev/video0 is available.{NC}")
        return True
    else:
        print(f"{YELLOW}! No camera device found.{NC}")
        print(f"{YELLOW}  Make sure your camera is connected and enabled.{NC}")
        return False
        
def check_required_commands():
    """Check if required commands are available."""
    print("Checking required commands...")
    
    required_commands = {
        'git': 'Git is required to clone the repository.',
        'python3': 'Python 3 is required to run the software.',
        'pip3': 'pip is required to install Python dependencies.',
        'nginx': 'Nginx is required for the web interface.'
    }
    
    missing_commands = []
    for cmd, desc in required_commands.items():
        if shutil.which(cmd) is None:
            missing_commands.append((cmd, desc))
            print(f"{YELLOW}! {cmd} is not available. {desc}{NC}")
        else:
            print(f"{GREEN}✓ {cmd} is available.{NC}")
    
    if missing_commands:
        print()
        print("Missing commands can be installed with:")
        print("sudo apt-get update")
        print(f"sudo apt-get install {' '.join(cmd for cmd, _ in missing_commands)}")
        return False
    
    return True

def check_network():
    """Check network connectivity."""
    print("Checking network connectivity...")
    
    try:
        # Try to ping Google's DNS server (8.8.8.8)
        result = subprocess.run(['ping', '-c', '1', '8.8.8.8'], 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                               text=True, check=False)
        
        if result.returncode == 0:
            print(f"{GREEN}✓ Network connection is available.{NC}")
            return True
        else:
            print(f"{YELLOW}! Network connection might not be available.{NC}")
            print(f"{YELLOW}  Internet access is required for installation.{NC}")
            return False
    except Exception as e:
        print(f"{YELLOW}! Could not check network connectivity: {e}{NC}")
        return False

def main():
    """Run all checks and provide a summary."""
    print_banner()
    
    checks = [
        ("Python version", check_python_version),
        ("Raspberry Pi", check_raspberry_pi),
        ("Camera", check_camera),
        ("Disk space", check_disk_space),
        ("Required commands", check_required_commands),
        ("Network connectivity", check_network)
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n[Checking {name}]")
        print("--------------------------------------------------")
        result = check_func()
        results.append((name, result))
        print()
    
    # Summary
    print("\n==================================================")
    print("PRE-INSTALLATION CHECK SUMMARY")
    print("==================================================")
    
    all_passed = True
    warnings = 0
    
    for name, result in results:
        if result is True:
            status = f"{GREEN}PASS{NC}"
        elif result is False:
            status = f"{RED}FAIL{NC}"
            all_passed = False
        else:
            status = f"{YELLOW}WARNING{NC}"
            warnings += 1
        
        print(f"{name:.<25} {status}")
    
    print("\n==================================================")
    
    if all_passed:
        print(f"{GREEN}All checks passed. Your system meets the requirements for CreatureBox.{NC}")
        print("\nYou can proceed with the installation.")
        return 0
    else:
        print(f"{RED}Some checks failed. Please address the issues before proceeding.{NC}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
