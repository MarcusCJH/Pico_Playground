"""
TX Baggage Demo - Configuration Template
-------------------------------------
Instructions:
1. Copy this file and rename it to 'config.py'
2. Replace the placeholder values with your actual settings
3. Upload config.py to your ReadPi device

DO NOT modify this template with real credentials!
"""

# WiFi Settings
# ------------
WIFI_SSID = "your-network"        # Your WiFi network name
WIFI_PASSWORD = "your-password"    # Your WiFi password

# Server Settings
# -------------
SERVER_IP = "192.168.0.197"       # Your server's IP address
SERVER_PORT = 8080                # Default port for the asset server

# RFID Card to Asset Mapping
# ------------------------
# Format: "CARD_ID": "ASSET_FILENAME"
CARD_ASSETS = {
    "3800132D9B9D": "1.mov",      # Demo video
    "38001370E9B2": "2.jpg",      # Demo image
    # Add more mappings as needed
} 