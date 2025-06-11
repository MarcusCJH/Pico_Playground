#!/bin/bash

# Configuration
REPO_URL="https://github.com/MarcusCJH/Pico_Playground.git"
TARGET_DIR="$HOME/Desktop/Pico_Playground"
ASSET_SERVER_DIR="$TARGET_DIR/src/tx_baggage"

echo "Setting up Asset Server on Desktop..."

# Create directories if they don't exist
mkdir -p "$TARGET_DIR"
mkdir -p "$ASSET_SERVER_DIR/assets"

# Clone or update repository
if [ ! -d "$TARGET_DIR/.git" ]; then
    echo "Cloning repository into Desktop..."
    git clone "$REPO_URL" "$TARGET_DIR"
else
    echo "Repository already exists on Desktop. Pulling latest changes..."
    cd "$TARGET_DIR"
    git pull
fi

# Make sure we're in the correct directory
cd "$ASSET_SERVER_DIR"

# Make the script executable
chmod +x asset_server.py

# Run the asset server
echo "Starting Asset Server..."
python3 asset_server.py 