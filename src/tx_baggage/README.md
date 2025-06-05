# TX Baggage Demo System

Interactive RFID demonstration system for exhibition displays.

## 📁 Contents

### Core Files
- **`asset_server.py`** - Asset server that handles videos and images
- **`readpi_client.py`** - RFID client for ReadPi device  
- **`web_player.html`** - Web interface for displaying content
- **`assets/`** - Media files (videos and images)
- **`config_template.py`** - Template for configuration settings
- **`config.py`** - Your actual configuration (not in version control)

## 🚀 Quick Start

### 1. Start the Server
```bash
python asset_server.py
```
Server will start at `http://your-ip:8080`

### 2. View in Browser
Open `http://your-ip:8080` to see the web player

### 3. Setup Configuration
1. Copy `config_template.py` to `config.py`
2. Edit settings in `config.py`
3. Upload to your ReadPi device

### 4. Deploy to ReadPi
Copy `readpi_client.py` and `config.py` to your ReadPi

## 📱 How It Works

1. **RFID Scan** → ReadPi detects card
2. **Send Request** → ReadPi sends asset filename to server  
3. **Display Content** → Web player shows video or image
4. **Auto Return** → Returns to welcome screen when done

## ⚙️ Configuration

### Setup Steps
1. Create `config.py` from template:
```python
# Copy from config_example.py and edit with your settings
WIFI_SSID = "your-network"        # Your WiFi name
WIFI_PASSWORD = "your-password"    # Your WiFi password
SERVER_IP = "192.168.0.197"       # Your server IP
SERVER_PORT = 8080                # Server port (default: 8080)

# RFID Card to Asset Mapping
CARD_ASSETS = {
    "3800132D9B9D": "1.mov",      # Video file
    "38001370E9B2": "2.jpg",      # Image file
}
```

2. Upload both `config.py` and `readpi_client.py` to your device
3. Keep `config.py` out of version control (it's in .gitignore)

### RFID Card Mapping
Edit `readpi_client.py`:
```python
self.card_assets = {
    "3800132D9B9D": "1.mov",      # Video file
    "38001370E9B2": "2.jpg",      # Image file
}
```

### Server Settings
Update IP address in `readpi_client.py`:
```python
self.SERVER_IP = "192.168.0.197"  # Your server IP
```

### WiFi Settings
Update credentials in `readpi_client.py`:
```python
self.WIFI_SSID = "your-network"
self.WIFI_PASSWORD = "your-password"
```

## 📂 Assets Folder

Put your media files in `assets/`:
- **Videos**: `.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`
- **Images**: `.jpg`, `.png`, `.gif`, `.bmp`, `.webp`

### Current Assets
- `1.mov` - Demo video
- `2.mov` - Demo video  
- `2.jpg` - Demo image

## 🎮 Controls

### Web Player
- **⚙️** - Show/hide controls
- **📊** - Toggle status overlay
- **🖥️** - Fullscreen mode
- **🔧** - Advanced test buttons

### Keyboard Shortcuts
- **C** - Toggle controls
- **S** - Toggle status
- **F** - Fullscreen
- **ESC** - Hide overlays

## 🔧 Features

### Asset Types
- **Videos** - Play normally until end
- **Images** - Display for 5 seconds with countdown

### Auto-Detection
- Server automatically detects file type
- Different handling for videos vs images
- Graceful error handling

### Real-time Updates
- Web player polls server every second
- Instant response to RFID triggers
- Status information display

## 📊 Status Information

The web player shows:
- Connection status
- Assets played count
- Last RFID card scanned
- Current asset playing
- Last update time

## 🛠️ Troubleshooting

### ReadPi Client Issues
1. Check WiFi connection
2. Verify server IP address
3. Test server ping: `http://server-ip:8080/ping`

### Web Player Issues
1. Check browser console (F12)
2. Verify asset files exist in `assets/` folder
3. Test direct asset access: `http://server-ip:8080/assets/filename`

### Server Issues
1. Check if port 8080 is available
2. Verify `assets/` folder exists
3. Check firewall settings

## 📝 Notes

- Images display for 60 seconds by default
- Videos play to completion
- RFID cards have 3-second cooldown
- Web player works offline once loaded
