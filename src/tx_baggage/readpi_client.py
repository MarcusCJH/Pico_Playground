"""
ReadPI Exhibition Client
Simple RFID scanner that triggers videos and images on a remote server
"""

import network
import urequests
import json
import time
from machine import Pin, SPI, PWM, UART
import st7789
import vga1_bold_16x32 as font
import config

class ReadPIClient:
    def __init__(self):
        # Configuration from config.py
        self.WIFI_SSID = config.WIFI_SSID
        self.WIFI_PASSWORD = config.WIFI_PASSWORD
        self.SERVER_IP = config.SERVER_IP
        self.SERVER_PORT = config.SERVER_PORT
        self.card_assets = config.CARD_ASSETS
        
        # Hardware Setup
        self.setup_hardware()
        self.setup_display()
        
        # State
        self.wifi_connected = False
        self.last_card = None
        self.last_scan_time = 0
        self.scan_cooldown = 3.0
        self.scan_count = 0
    
    def setup_hardware(self):
        """Initialize hardware components"""
        self.led = Pin("LED", Pin.OUT)
        self.buzzer = PWM(Pin(15))
        self.uart = UART(1, baudrate=9600, bits=8, parity=None, stop=1)
    
    def setup_display(self):
        """Initialize the display"""
        spi = SPI(1, baudrate=40000000, sck=Pin(10), mosi=Pin(11))
        self.display = st7789.ST7789(
            spi, 240, 240,
            reset=Pin(12, Pin.OUT),
            cs=Pin(9, Pin.OUT),
            dc=Pin(8, Pin.OUT),
            backlight=Pin(13, Pin.OUT),
            rotation=1
        )
        self.display.init()
        self.show_startup()
    
    def beep(self, frequency=1000, duration=0.1):
        """Play a beep sound"""
        self.buzzer.duty_u16(3000)
        self.buzzer.freq(frequency)
        time.sleep(duration)
        self.buzzer.duty_u16(0)
    
    def show_startup(self):
        """Show startup screen"""
        self.display.fill(0)
        self.display.text(font, "EXHIBITION", 40, 30, st7789.CYAN)
        self.display.text(font, "ASSET SYSTEM", 30, 60, st7789.CYAN)
        self.display.fill_rect(0, 90, 240, 3, st7789.CYAN)
        self.display.text(font, "Starting...", 50, 120, st7789.YELLOW)
    
    def show_status(self, message, color=st7789.WHITE, line=0):
        """Update status line on display"""
        y = 100 + (line * 20)
        self.display.fill_rect(0, y, 240, 18, st7789.BLACK)
        self.display.text(font, message[:15], 10, y, color)
        print(f"Status: {message}")
    
    def connect_wifi(self):
        """Connect to WiFi"""
        self.show_status("Connecting WiFi...", st7789.YELLOW, 1)
        
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        
        if not wlan.isconnected():
            wlan.connect(self.WIFI_SSID, self.WIFI_PASSWORD)
            
            # Wait for connection
            timeout = 15
            while not wlan.isconnected() and timeout > 0:
                self.led.toggle()
                time.sleep(0.5)
                timeout -= 1
        
        if wlan.isconnected():
            self.wifi_connected = True
            ip = wlan.ifconfig()[0]
            self.show_status("WiFi Connected", st7789.GREEN, 1)
            self.show_status(f"IP: {ip[:12]}", st7789.WHITE, 2)
            self.beep(1000, 0.1)
            return True
        else:
            self.show_status("WiFi Failed", st7789.RED, 1)
            self.beep(500, 0.5)
            return False
    
    def test_server(self):
        """Test connection to asset server"""
        try:
            self.show_status("Testing Server...", st7789.YELLOW, 3)
            url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/ping"
            print(f"Testing server at: {url}")
            response = urequests.get(url, timeout=5)
            
            if response.status_code == 200:
                self.show_status("Server OK", st7789.GREEN, 3)
                self.beep(1200, 0.1)
                response.close()
                return True
            else:
                raise Exception(f"Server error: {response.status_code}")
                
        except Exception as e:
            self.show_status("Server Failed", st7789.RED, 3)
            print(f"Server test failed: {e}")
            print(f"Make sure asset server is running at {self.SERVER_IP}:{self.SERVER_PORT}")
            return False
    
    def show_ready(self):
        """Show ready screen"""
        self.display.fill(0)
        
        self.display.text(font, "READY TO SCAN", 20, 20, st7789.GREEN)
        self.display.fill_rect(0, 50, 240, 2, st7789.GREEN)
        
        self.display.text(font, "Hold RFID card", 25, 80, st7789.WHITE)
        self.display.text(font, "near reader", 45, 110, st7789.WHITE)
        self.display.text(font, "3sec cooldown", 25, 130, st7789.CYAN)
        
        self.display.text(font, f"WiFi: OK", 10, 160, st7789.GREEN)
        self.display.text(font, f"Server: OK", 10, 180, st7789.GREEN)
        self.display.text(font, f"Scans: {self.scan_count}", 10, 200, st7789.CYAN)
    
    def show_card_scanned(self, card_id, asset_file):
        """Show feedback when card is scanned"""
        self.display.fill_rect(0, 80, 240, 80, st7789.BLACK)
        
        self.display.text(font, "CARD SCANNED!", 20, 80, st7789.GREEN)
        self.display.text(font, f"ID: {card_id[:10]}", 10, 110, st7789.YELLOW)
        self.display.text(font, f"File: {asset_file[:10]}", 10, 140, st7789.CYAN)
        self.display.text(font, f"Count: {self.scan_count}", 10, 170, st7789.WHITE)
        
        # Success sound
        for freq in [1000, 1200, 1500]:
            self.beep(freq, 0.1)
        
        time.sleep(1.5)
        self.show_ready()
    
    def show_unknown_card(self, card_id):
        """Show feedback for unknown cards"""
        self.display.fill_rect(0, 80, 240, 80, st7789.BLACK)
        
        self.display.text(font, "UNKNOWN CARD", 20, 80, st7789.RED)
        self.display.text(font, f"ID: {card_id[:10]}", 10, 110, st7789.YELLOW)
        self.display.text(font, "Not configured", 10, 140, st7789.WHITE)
        
        # Error sound
        self.beep(400, 0.5)
        
        time.sleep(2)
        self.show_ready()
    
    def trigger_asset(self, card_id, asset_file):
        """Send asset trigger command to server"""
        try:
            url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/play"
            data = {
                "asset_file": asset_file,
                "card_id": card_id,
                "timestamp": time.time()
            }
            
            response = urequests.post(
                url, 
                data=json.dumps(data),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            success = response.status_code == 200
            response.close()
            return success
            
        except Exception as e:
            print(f"Failed to trigger asset: {e}")
            return False
    
    def process_card(self, card_id):
        """Process scanned RFID card"""
        card_id = card_id.strip()
        current_time = time.time()
        
        # Check cooldown
        if card_id == self.last_card and (current_time - self.last_scan_time) < self.scan_cooldown:
            return
        
        self.last_card = card_id
        self.last_scan_time = current_time
        self.scan_count += 1
        
        print(f"Card scanned: {card_id} (Scan #{self.scan_count})")
        
        asset_file = self.card_assets.get(card_id)
        
        if asset_file:
            print(f"Triggering asset: {asset_file}")
            if self.trigger_asset(card_id, asset_file):
                self.show_card_scanned(card_id, asset_file)
            else:
                self.show_status("Send Failed", st7789.RED, 4)
                self.beep(500, 0.3)
        else:
            print(f"Unknown card: {card_id}")
            self.show_unknown_card(card_id)
    
    def run(self):
        """Main loop"""
        print("Starting ReadPI Exhibition Client...")
        
        if not self.connect_wifi():
            print("WiFi connection failed!")
            return
        
        if not self.test_server():
            print("Server connection failed!")
        
        self.show_ready()
        
        print("Ready to scan RFID cards!")
        print("Mapped assets:")
        for card_id, asset_file in self.card_assets.items():
            print(f"  {card_id} -> {asset_file}")
        
        try:
            while True:
                data = self.uart.read(12)
                if data:
                    try:
                        card_id = data.decode("utf-8")
                        self.process_card(card_id)
                    except UnicodeDecodeError:
                        print("Error decoding RFID data")
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("Client stopped")
            self.display.fill(0)
            self.display.text(font, "STOPPED", 60, 100, st7789.RED)

def main():
    client = ReadPIClient()
    client.run()

if __name__ == "__main__":
    main() 