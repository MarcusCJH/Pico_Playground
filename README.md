
## Raspberry Pi Pico W Integration (Work in Progress) 🚧

**WIP YO**


# Asset Server for Raspberry Pi 5

A simple HTTP server for playing videos and images triggered by RFID cards.


## Setup Instructions for Raspberry Pi 5

1. Make sure your Raspberry Pi 5 is set up with Raspberry Pi OS and has internet connection.

2. Install required packages:
```bash
sudo apt update
sudo apt install -y git python3 python3-pip
```

3. Download the setup script to your Desktop:
```bash
cd ~/Desktop
wget https://raw.githubusercontent.com/MarcusCJH/Pico_Playground/main/setup_and_run.sh
chmod +x setup_and_run.sh
```

4. Run the setup script:
```bash
./setup_and_run.sh
```

The script will:
- Clone or update the repository on your Desktop
- Set up the assets directory
- Start the asset server

## Usage

- The server will run on port 8080
- Access the web interface at: `http://[raspberry-pi-ip]:8080`
- Place your video and image files in the `Desktop/Pico_Playground/src/tx_baggage/assets` directory
- The server supports:
  - Videos: .mp4, .avi, .mov, .mkv, .wmv, .flv, .m4v, .webm
  - Images: .jpg, .jpeg, .png, .gif, .bmp, .webp, .svg

## Troubleshooting

- View logs in `Desktop/Pico_Playground/src/tx_baggage/asset_server.log`

## Controls

- Press Ctrl+C to stop the server
- The terminal window will stay open until you press Enter 