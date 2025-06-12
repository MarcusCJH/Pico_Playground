"""
Configuration Template for Exhibition System

1. Copy this file to config.py
2. Update the settings below with your values
3. Upload config.py to your PicoRFID device

DO NOT commit config.py to version control!
"""

# WiFi Settings
# ------------
WIFI_SSID = "your-wifi-network"        # Your WiFi network name
WIFI_PASSWORD = "your-wifi-password"    # Your WiFi password

# Server Settings
# -------------
SERVER_IP = "192.168.1.100"       # Your server's IP address
SERVER_PORT = 8080                # Default port for the asset server

# RFID Card to Asset Mapping
# ------------------------
# Format: "CARD_ID": "ASSET_FILENAME"
CARD_ASSETS = {
    "example-card-id-1": "video1.mp4",
    "example-card-id-2": "image1.jpg",
    "example-card-id-3": "video2.mov",
}

# Example card IDs (replace with your actual card IDs):
# "3800132D9B9D": "demo_video.mp4",
# "38001370E9B2": "demo_image.jpg",

# To find your card IDs:
# 1. Run the client without mappings
# 2. Scan your cards - the IDs will be printed to console
# 3. Add the IDs to CARD_ASSETS above 