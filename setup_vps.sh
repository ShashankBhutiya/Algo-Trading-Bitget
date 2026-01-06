#!/bin/bash

# Bitget Bot VPS Setup Script
# Usage: ./setup_vps.sh

echo "-----------------------------------"
echo "  Bitget Bot - VPS Auto Setup"
echo "-----------------------------------"

# 1. Update System
echo "[1/5] Updating System Packages..."
sudo apt update && sudo apt install -y python3-pip python3-venv git

# 2. Setup Virtual Environment (Optional, here we install globally for simplicity or use venv)
# Using global pip for simplicity in this script, or install user-local.
echo "[2/5] Installing Dependencies..."
pip3 install -r requirements.txt

# 3. Permissions
echo "[3/5] Setting Permissions..."
chmod +x run_bot.py
# chmod +x *.sh

# 4. Systemd Setup
echo "[4/5] Configuring System Service..."

# Check if service file exists in current dir
if [ -f "bitget_bot.service" ]; then
    # Modify the WorkingDirectory in the service file to currentPWD
    CUR_DIR=$(pwd)
    echo "    > Setting WorkingDictionary to $CUR_DIR"
    
    # Use sed to replace the placeholder path with actual current path
    sed -i "s|WorkingDirectory=/root/bitget_bot|WorkingDirectory=$CUR_DIR|g" bitget_bot.service
    
    # Update ExecStart to look for python3 in standard location, or venv if used.
    # We assume 'python3' is in path.
    # sed -i "s|ExecStart=/usr/bin/python3|ExecStart=$(which python3)|g" bitget_bot.service
    
    echo "    > Copying service file to /etc/systemd/system/"
    sudo cp bitget_bot.service /etc/systemd/system/bitget_bot.service
    
    echo "    > Reloading Daemon"
    sudo systemctl daemon-reload
    
    echo "    > Enabling Service (Auto-start on boot)"
    sudo systemctl enable bitget_bot
    
    echo "    > Starting Service NOW"
    sudo systemctl restart bitget_bot
    
    echo "✅ Service Started!"
    sudo systemctl status bitget_bot --no-pager
else
    echo "❌ Error: 'bitget_bot.service' file not found in directory!"
fi

echo "-----------------------------------"
echo "Setup Complete!"
echo "View logs with: tail -f logs/strategy_bot.log"
echo "-----------------------------------"
