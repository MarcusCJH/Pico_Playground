# TX Baggage Exhibition System

A complete RFID-triggered multimedia exhibition system using Raspberry Pi Pico W.

## Files

- **`pico_expander_client.py`** - RFID client for custom Pico board with RC522
- **`asset_server.py`** - HTTP server that plays videos/images
- **`web_player.html`** - Web interface for asset playback
- **`web_manager.html`** - Management interface for uploads and config
- **`config.py`** - Configuration file with WiFi and asset mappings
- **`config_example.py`** - Example configuration template
- **`readpi_client_backup.py`** - Legacy client for different hardware (backup)

## Quick Start

### 1. Setup Asset Server
```bash
cd src/tx_baggage
python3 asset_server.py
```

### 2. Configure System
1. Copy `config_example.py` to `config.py`
2. Update WiFi credentials and server IP
3. Upload to your Pico device

### 3. Access Interfaces
- **Player**: `http://server-ip:8080/` 
- **Manager**: `http://server-ip:8080/manage`

### 4. Deploy to Pico
1. Install MicroPython on your Raspberry Pi Pico W
2. Upload both `config.py` and `pico_expander_client.py` to your device
3. Rename `pico_expander_client.py` to `main.py` on the device

## How It Works

1. **RFID Scan** → Pico detects card with RC522 reader
2. **Send Request** → Pico sends card ID to server  
3. **Play Assets** → Server plays first asset, navigation available for multiple assets
4. **Card Removal** → Automatically returns to splash screen when card removed
5. **Audio/Visual Feedback** → Pico provides LED and buzzer feedback

## Configuration

### WiFi Settings
```python
WIFI_SSID = "your-network"
WIFI_PASSWORD = "your-password"
```

### Server Settings  
```python
SERVER_IP = "192.168.1.100"
SERVER_PORT = 8080
```

### Card Mappings (Updated Format)
```python
CARD_ASSETS = {
    "9b:8a:49:06:5e": ["1.mov"],  # 1 asset
    "88:04:e1:11:7c": ["2.jpg", "3.mov"],  # 2 assets  
    "3c:04:1c:06:22": ["4.png", "image.jpg", "1.mov"]  # 3 assets
}
```

**New Features:**
- ✅ **Multiple assets per card** - Cards can now have multiple files
- ✅ **Card-based navigation** - Navigate through current card's assets only
- ✅ **Auto return to splash** - Removing card returns to welcome screen

## Hardware Setup

### Custom Pico Board with RC522
Pin connections for the RC522 RFID reader:
- VCC/3.3V → 3.3V (Power)
- GND → GND (Ground)  
- RST → GP5 (Reset pin)
- SDA/CS → GP1 (SPI Chip Select)
- SCK → GP2 (SPI Clock)
- MOSI → GP3 (SPI Master Out Slave In)
- MISO → GP0 (SPI Master In Slave Out)

Feedback components:
- LED → GP21 (Visual feedback)
- Buzzer → GP15 (Audio feedback)

## RFID Card Management

### New Features ✨

The system now automatically tracks **all RFID card scans** (both known and unknown cards) and provides an easy web interface to map unknown cards to assets.

### How It Works

1. **Scan Any RFID Card** → Client sends card ID to server (even unknown cards)
2. **Server Tracks All Cards** → Unknown cards are logged with scan timestamps
3. **Easy Mapping** → Use the Management Interface to map unknown cards to assets
4. **Auto-Config Update** → Card mappings are automatically added to `config.py`

### Management Interface

Access the management interface at: `http://server-ip:8080/manage`

**New RFID Card Management Section:**
- 📊 **Unknown Cards Table** - Shows cards that need mapping
- 🎯 **Quick Mapping** - Select asset from dropdown to map cards
- 📈 **All Scanned Cards** - View all card activity with timestamps
- 🔄 **Auto-Refresh** - Real-time updates of card scans

### Workflow for Adding New Cards

1. **Scan Unknown Card** → Pico client detects new card
2. **Check Management Interface** → Card appears in "Unknown Cards" table
3. **Map to Asset** → Select asset file from dropdown
4. **Auto-Update Config** → `config.py` is automatically updated
5. **Ready to Use** → Card now triggers the mapped asset

### API Endpoints

New endpoints for RFID management:
- `GET /scanned-cards` - Get all scanned card data
- `GET /unknown-cards` - Get only unknown cards
- `POST /unknown-card` - Log unknown card scan

### Benefits

- ✅ **No More Manual Config Editing** - Point-and-click card mapping
- ✅ **See All Card Activity** - Track when cards were first/last scanned
- ✅ **Never Lose Unknown Cards** - All scans are logged automatically
- ✅ **Real-time Updates** - Management interface shows live data
- ✅ **Easy Troubleshooting** - See exactly which cards are being scanned

## Asset Management

### Supported Formats
- **Videos**: .mp4, .mov, .avi, .mkv, .webm
- **Images**: .jpg, .png, .gif, .bmp, .webp

### Web Management Interface
Visit `http://server-ip:8080/manage` to:
- Upload new assets
- View current assets
- Edit RFID card mappings
- Update configuration

### Manual Upload
Copy files directly to the `assets/` folder on the server.

## API Endpoints

### Asset Server
- `GET /` - Web player interface
- `GET /manage` - Management interface  
- `GET /assets` - List all assets
- `GET /assets/{filename}` - Serve asset file
- `GET /status` - Server status
- `GET /current-asset` - Currently playing asset
- `POST /play` - Trigger asset playback
- `POST /upload` - Upload new asset
- `POST /update-config` - Update configuration

### Example API Usage
```bash
# Trigger asset playback
curl -X POST http://server-ip:8080/play \
  -H "Content-Type: application/json" \
  -d '{"asset_file": "video1.mp4", "card_id": "12345"}'

# Get server status  
curl http://server-ip:8080/status
```

## Hardware Requirements

### PicoRFID Device
- Raspberry Pi Pico W
- RFID reader module (125KHz or RC522)
- ST7789 display
- Buzzer
- LED indicators

### Server
- Any computer/server with Python 3.6+
- Network connection
- Web browser for interface

## Troubleshooting

### PicoRFID Client Issues
- Check WiFi credentials in config.py
- Verify server IP address is correct
- Ensure server is running and accessible
- Check RFID card mappings

### Server Issues  
- Verify port 8080 is not in use
- Check assets folder permissions
- Ensure media files are in supported formats
- Check network connectivity

### Network Issues
- Verify all devices on same network
- Check firewall settings
- Test with ping/curl commands
- Verify IP addresses are correct

## Development

### Adding New Features
1. Modify client code for new RFID behavior
2. Add server endpoints for new functionality  
3. Update web interfaces as needed
4. Test with actual hardware

### File Structure
```
tx_baggage/
├── pico_expander_client.py      # PicoRFID client
├── asset_server.py          # HTTP server
├── web_player.html          # Playback interface
├── web_manager.html         # Management interface
├── config.py               # Configuration
├── assets/                 # Media files
└── README.md              # This file
```
