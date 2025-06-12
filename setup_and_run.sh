#!/bin/bash
# TX Baggage Exhibition System - Raspberry Pi 5 Setup & Run Script

# Configuration
REPO_URL="https://github.com/MarcusCJH/Pico_Playground.git"
TARGET_DIR="$HOME/Desktop/Pico_Playground"
ASSET_DIR="$TARGET_DIR/src/tx_baggage"

# Clear screen
clear
echo "🎬 Setting up TX Baggage Exhibition System on Raspberry Pi 5..."
echo ""

# Clone or update repository
if [ ! -d "$TARGET_DIR/.git" ]; then
    echo "📥 Cloning repository to Desktop..."
    rm -rf "$TARGET_DIR"
    git clone "$REPO_URL" "$TARGET_DIR"
    echo "✅ Repository cloned successfully"
else
    echo "🔄 Repository exists. Updating..."
    cd "$TARGET_DIR"
    git pull
    echo "✅ Repository updated"
fi

# Navigate to asset directory
cd "$ASSET_DIR"
echo "📁 Working directory: $(pwd)"

# Check if config.py exists, create from example if needed
if [ ! -f "config.py" ]; then
    echo "⚠️  config.py not found. Creating from example..."
    if [ -f "config_example.py" ]; then
        cp config_example.py config.py
        echo "✅ Created config.py from example. Please edit it with your settings."
    else
        echo "❌ config_example.py not found. Cannot create config.py"
        exit 1
    fi
else
    echo "✅ config.py already exists"
fi

# Create assets directory if it doesn't exist
mkdir -p assets
echo "✅ Assets directory ready"

# Start the server
echo "🚀 Starting asset server..."
python3 asset_server.py

# Keep window open after server stops
echo ""
echo "🛑 Server stopped. Press Enter to close..."
read 