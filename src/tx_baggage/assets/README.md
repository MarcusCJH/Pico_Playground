TX BAGGAGE DEMO SYSTEM - ASSETS FOLDER
=====================================

This folder contains media files for the TX Baggage Exhibition System.

Supported Formats
-----------------
Videos: .mp4, .mov, .avi, .mkv, .wmv, .flv, .m4v, .webm
Images: .jpg, .jpeg, .png, .gif, .bmp, .webp, .svg

Current Demo Files
------------------
- 1.mov - Demo video (mapped to card 3800132D9B9D)
- 2.jpg - Demo image (mapped to card 38001370E9B2)  
- 3.mov - Demo video (mapped to card 38001370E9B3)
- 4.png - Demo image (unmapped)
- Tough-Cats-With-those-buddies-you-389.jpg - Demo image (unmapped)

Management
----------
1. Upload files via Web Manager: http://server-ip:8080/manage
2. Map RFID cards to assets using the management interface
3. Unknown cards are automatically tracked for easy mapping
4. Files can be renamed/deleted through the web interface

RFID Card Mapping
-----------------
Cards are mapped in config.py under CARD_ASSETS:
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