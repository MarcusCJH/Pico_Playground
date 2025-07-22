RFID EXHIBITION SYSTEM - ASSETS FOLDER
=====================================

This folder contains media files for the RFID Exhibition System.

Supported Formats
-----------------
Videos: .mp4, .mov, .avi, .mkv, .wmv, .flv, .m4v, .webm
Images: .jpg, .jpeg, .png, .gif, .bmp, .webp, .svg

Current Demo Files
------------------
- 1.mov - Demo video (card 9b:8a:49:06:5e)
- 2.jpg - Demo image (card 88:04:e1:11:7c)  
- 3.mov - Demo video (card 88:04:e1:11:7c)
- 4.png - Demo image (card 3c:04:1c:06:22)
- Tough-Cats-With-those-buddies-you-389.jpg - Demo image (card 3c:04:1c:06:22)
- splash.png - Splash screen image (shown after first interaction when no card is present)

Splash Screen
-------------
The web player now supports a splash screen that appears after the first interaction:
- Create a file named "splash.png", "splash.jpg", or "splash.jpeg" in this assets folder
- The splash screen will be displayed full-screen when no RFID card is present (after first use)
- If no splash image is found, the system falls back to the original welcome screen
- The welcome screen is only shown on the very first visit to the player

Management
----------
1. Upload files via Web Manager: http://server-ip:8080/manage
2. Map RFID cards to assets using the management interface
3. Unknown cards are automatically tracked for easy mapping
4. Files can be renamed/deleted through the web interface

RFID Card Mapping
-----------------
Cards are mapped in config.py under CARD_ASSETS (now supports multiple assets per card):
- Each card can have multiple assets: `["file1.mov", "file2.jpg"]`
- Navigate through card's assets with Previous/Next buttons
- Scan unknown cards to see them in the management interface
- Use dropdown menus to map cards to assets
- Configuration is automatically updated

Testing
-------
- Web Player: http://server-ip:8080/
- Management: http://server-ip:8080/manage
- Direct asset access: http://server-ip:8080/assets/filename

Notes
-----
- Files are served directly by the asset server
- Large files (>50MB) may cause slower loading
- Keep backup copies of important media files 