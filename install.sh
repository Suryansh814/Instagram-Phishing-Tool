#!/bin/bash

echo "Installing Instagram Phishing Tool..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit
fi

# Update system
apt update

# Install required packages
apt install -y python3 python3-pip git

# Install Python dependencies
pip3 install -r requirements.txt

# Create directories for static files
mkdir -p templates static

# Make the script executable
chmod +x app.py

echo "Installation completed successfully!"
echo "Run 'python3 app.py' to start the tool"
