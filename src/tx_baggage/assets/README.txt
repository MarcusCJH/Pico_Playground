ASSETS FOLDER
=============

This folder contains media files for the TX Baggage Demo System.

Supported Formats
---------------
Videos:
- MP4 (recommended)
- MOV
- AVI
- MKV
- WEBM

Images:
- JPG/JPEG
- PNG
- GIF
- WEBP

Git Management
-------------
Media files in this folder are NOT tracked by git due to their size.
When deploying:
1. Manually copy your media files to this directory
2. Make sure filenames match your config.py CARD_ASSETS mapping
3. Keep files under 50MB when possible

Current Demo Files
----------------
- 1.mov - Demo video
- 2.mov - Demo video
- 2.jpg - Demo image

Usage
-----
1. Place your media files in this folder
2. Update CARD_ASSETS in config.py to match your filenames
3. The server will automatically detect and serve these files
4. Test each file by accessing: http://server-ip:8080/assets/filename

Notes
-----
- Keep backup copies of your media files elsewhere
- Consider using compressed formats for better performance
- Test your media files before deployment 