#!/bin/bash
# RFID Exhibition System - Raspberry Pi 5 Setup & Run Script

# Configuration
REPO_URL="https://github.com/MarcusCJH/Pico_Playground.git"
TARGET_DIR="$HOME/Desktop/Pico_Playground"
ASSET_DIR="$TARGET_DIR/src/exhibition_system"
FIXED_PORT="8080"

# Get local IP address automatically
get_local_ip() {
    # Try multiple methods to get the local IP
    local ip=""
    
    # Method 1: hostname -I (most reliable on Raspberry Pi)
    if command -v hostname >/dev/null 2>&1; then
        ip=$(hostname -I | awk '{print $1}')
    fi
    
    # Method 2: ip route (fallback)
    if [ -z "$ip" ] && command -v ip >/dev/null 2>&1; then
        ip=$(ip route get 8.8.8.8 2>/dev/null | grep -oP 'src \K\S+')
    fi
    
    # Method 3: ifconfig (fallback)
    if [ -z "$ip" ] && command -v ifconfig >/dev/null 2>&1; then
        ip=$(ifconfig | grep -E "inet [0-9]" | grep -v "127.0.0.1" | awk '{print $2}' | head -1)
    fi
    
    # Method 4: NetworkManager (fallback)
    if [ -z "$ip" ] && command -v nmcli >/dev/null 2>&1; then
        ip=$(nmcli -t -f IP4.ADDRESS dev show | head -1 | cut -d: -f2 | cut -d/ -f1)
    fi
    
    echo "$ip"
}

# Get the local IP address
LOCAL_IP=$(get_local_ip)

# Clear screen
clear
echo "Setting up RFID Exhibition System on Raspberry Pi 5..."
echo "Auto-detected IP: $LOCAL_IP:$FIXED_PORT"
echo ""

# Clone or update repository
if [ ! -d "$TARGET_DIR/.git" ]; then
    echo "[INFO] Cloning repository to Desktop..."
    rm -rf "$TARGET_DIR"
    git clone "$REPO_URL" "$TARGET_DIR"
    echo "[OK] Repository cloned successfully"
else
    echo "[INFO] Repository exists. Updating..."
    cd "$TARGET_DIR"
    git pull
    echo "[OK] Repository updated"
fi

# Navigate to asset directory
cd "$ASSET_DIR"
echo "[INFO] Working directory: $(pwd)"

# Check if config.py exists, create from example if needed
if [ ! -f "config.py" ]; then
    echo "[WARN] config.py not found. Creating from example..."
    if [ -f "config_example.py" ]; then
        cp config_example.py config.py
        echo "[OK] Created config.py from example. Please edit it with your settings."
    else
        echo "[ERROR] config_example.py not found. Cannot create config.py"
        exit 1
    fi
else
    echo "[OK] config.py already exists"
fi

# Create assets directory if it doesn't exist
mkdir -p assets
echo "[OK] Assets directory ready"

# Start the server
echo "[INFO] Starting asset server on $LOCAL_IP:$FIXED_PORT..."
echo "[INFO] Server will be accessible at: http://$LOCAL_IP:$FIXED_PORT"

# Always run in auto mode (open browser in fullscreen)
AUTO_OPEN_BROWSER="true"

if [ "$AUTO_OPEN_BROWSER" = "true" ] || [ "$AUTO_OPEN_BROWSER" = "auto" ]; then
    echo "[INFO] Auto-start mode: Will open browser in fullscreen after server starts"
    
    # Start server in background
    python3 asset_server.py &
    SERVER_PID=$!
    
    echo "[INFO] Server started in background (PID: $SERVER_PID)"
    
    # Wait for server to be ready
    echo "[INFO] Waiting for server to start..."
    sleep 15
    
    # Check if server is responding
    echo "[INFO] Checking if server is ready..."
    for i in {1..10}; do
        if curl -s http://$LOCAL_IP:$FIXED_PORT/ping > /dev/null 2>&1; then
            echo "[OK] Server is ready!"
            break
        else
            echo "[INFO] Server not ready yet, attempt $i/10..."
            sleep 3
        fi
    done
    
    # Final check
    if ! curl -s http://$LOCAL_IP:$FIXED_PORT/ping > /dev/null 2>&1; then
        echo "[ERROR] Server failed to start properly"
        echo "[ERROR] Check the server logs and try again"
        exit 1
    fi
    
    # Open browser in fullscreen mode
    echo "[INFO] Opening browser in fullscreen mode..."
    echo "[INFO] URL: http://$LOCAL_IP:$FIXED_PORT"
    
    # Detect operating system and use appropriate browser command
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS - use Chrome
        echo "[INFO] Detected macOS - using Chrome"
        pkill -f "Google Chrome" 2>/dev/null || true
        sleep 2
        open -a "Google Chrome" --args \
            --kiosk \
            --no-sandbox \
            --disable-web-security \
            --disable-gpu-sandbox \
            --disable-software-rasterizer \
            --user-data-dir=/tmp/chrome-exhibition \
            --memory-pressure-off \
            --max_old_space_size=4096 \
            --disable-background-timer-throttling \
            --disable-renderer-backgrounding \
            --disable-backgrounding-occluded-windows \
            --disable-features=TranslateUI \
            --disable-ipc-flooding-protection \
            "http://$LOCAL_IP:$FIXED_PORT/"
    else
        # Linux (Raspberry Pi) - use Firefox
        echo "[INFO] Detected Linux - using Firefox"
        pkill -f firefox 2>/dev/null || true
        sleep 2
        
        # Start Firefox in fullscreen mode (non-kiosk)
        firefox \
            --private-window \
            --no-remote \
            --new-instance \
            "http://$LOCAL_IP:$FIXED_PORT/" &
        
        FIREFOX_PID=$!
        echo "[INFO] Firefox started (PID: $FIREFOX_PID)"
        
        # Wait for Firefox to load
        echo "[INFO] Waiting for Firefox to load..."
        sleep 5
        
        # Use xdotool to press F11 for fullscreen (can be exited with ESC/F11)
        echo "[INFO] Entering fullscreen mode..."
        if command -v xdotool >/dev/null 2>&1; then
            xdotool key F11
            echo "[INFO] Fullscreen mode activated (press ESC or F11 to exit)"
        else
            echo "[WARN] xdotool not available - please press F11 manually for fullscreen"
            echo "[INFO] You can exit fullscreen with ESC or F11"
        fi
    fi
    
    BROWSER_PID=$!
    
    echo "[OK] Browser opened in fullscreen (PID: $BROWSER_PID)"
    echo ""
    echo "=========================================="
    echo "🎉 Exhibition system is now running!"
    echo "=========================================="
    echo "   - Server: http://$LOCAL_IP:$FIXED_PORT"
    echo "   - Browser: Fullscreen mode"
    echo "   - Press Ctrl+C to stop"
    echo "=========================================="
    echo ""
    
    # Keep the script running and monitor the server
    trap 'echo ""; echo "[INFO] Stopping exhibition system..."; kill $SERVER_PID $BROWSER_PID 2>/dev/null; exit 0' INT
    
    # Monitor server process
    while kill -0 $SERVER_PID 2>/dev/null; do
        sleep 5
    done
    
    echo "[ERROR] Server process ended unexpectedly"
    echo "[INFO] Restarting in 10 seconds..."
    sleep 10
    exec "$0"  # Restart the script
fi 