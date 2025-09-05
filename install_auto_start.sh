#!/bin/bash
# Installation script for RFID Exhibition System Auto-Start

echo "=========================================="
echo "🔧 Installing RFID Exhibition System Auto-Start"
echo "=========================================="

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "⚠️  Warning: This doesn't appear to be a Raspberry Pi"
    echo "   The installation may not work correctly"
    echo ""
fi

# Make scripts executable
echo "📝 Making scripts executable..."
chmod +x /home/rpi5/Desktop/setup_and_run.sh
chmod +x "/home/rpi5/Desktop/Start Exhibition System.desktop"

# Copy service file
echo "📋 Installing systemd service..."
sudo cp exhibition-auto-start.service /etc/systemd/system/

# Reload systemd
echo "🔄 Reloading systemd..."
sudo systemctl daemon-reload

# Enable the service
echo "✅ Enabling auto-start service..."
sudo systemctl enable exhibition-auto-start.service

echo ""
echo "🎉 Installation complete!"
echo ""
echo "=========================================="
echo "📋 What's been set up:"
echo "=========================================="
echo "✅ Main script: /home/rpi5/Desktop/setup_and_run.sh"
echo "✅ Desktop shortcut: 'Start Exhibition System'"
echo "✅ Systemd service: exhibition-auto-start.service"
echo "✅ Auto-start enabled: Will start on boot"
echo ""
echo "=========================================="
echo "🚀 How to use:"
echo "=========================================="
echo "1. Manual start: Double-click 'Start Exhibition System' on desktop"
echo "2. Manual start: Run './setup_and_run.sh' in terminal"
echo "3. Auto start: The system will start automatically on next boot"
echo "4. Check status: sudo systemctl status exhibition-auto-start.service"
echo "5. View logs: journalctl -u exhibition-auto-start.service -f"
echo ""
echo "=========================================="
echo "⚙️  Management commands:"
echo "=========================================="
echo "• Disable auto-start: sudo systemctl disable exhibition-auto-start.service"
echo "• Stop service: sudo systemctl stop exhibition-auto-start.service"
echo "• Start service: sudo systemctl start exhibition-auto-start.service"
echo "• Restart service: sudo systemctl restart exhibition-auto-start.service"
echo ""
echo "🎯 The exhibition system will now:"
echo "   - Start automatically when Pi boots up"
echo "   - Run setup_and_run.sh to start the server"
echo "   - Open browser in fullscreen mode"
echo "   - Point to http://192.168.0.106:8080"
echo ""
echo "Ready to test! You can start it now or reboot to test auto-start."
