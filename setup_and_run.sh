#!/bin/bash

# Configuration
REPO_URL="https://github.com/MarcusCJH/Pico_Playground.git"
TARGET_DIR="$HOME/Desktop/Pico_Playground"
ASSET_DIR="$TARGET_DIR/src/tx_baggage"

# Clear screen
clear
echo "Setting up Asset Server..."

# Clone or update repository
if [ ! -d "$TARGET_DIR/.git" ]; then
    echo "Cloning repository to Desktop..."
    rm -rf "$TARGET_DIR"
    git clone "$REPO_URL" "$TARGET_DIR"
else
    echo "Repository exists. Updating..."
    cd "$TARGET_DIR"
    git pull
fi

# Create assets directory
mkdir -p "$ASSET_DIR/assets"

# Make script executable
cd "$ASSET_DIR"
chmod +x asset_server.py

# Run server
echo "Server starting at http://localhost:8080"
echo "Press Ctrl+C to stop"
echo ""
python3 asset_server.py

# Keep window open
echo ""
echo "Server stopped. Press Enter to close..."
read 