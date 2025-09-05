#!/bin/bash
# Install xdotool for F11 key automation

echo "Installing xdotool for F11 key automation..."

# Update package list
sudo apt update

# Install xdotool
sudo apt install -y xdotool

echo "✅ xdotool installed successfully!"
echo ""
echo "xdotool will automatically press F11 to enter fullscreen mode."
echo "You can exit fullscreen by pressing ESC or F11."
