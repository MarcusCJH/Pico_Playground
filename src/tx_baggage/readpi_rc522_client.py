"""
ReadPI Exhibition Client - RC522 Version
Simple RFID scanner using RC522 that triggers videos and images on a remote server
"""

import network
import urequests
import json
import time
from machine import Pin, SPI, PWM
import st7789
import vga1_bold_16x32 as font
import config

class MFRC522:
    NRSTPD = 22
    MAX_LEN = 16

    PCD_IDLE = 0x00
    PCD_AUTHENT = 0x0E
    PCD_RECEIVE = 0x08
    PCD_TRANSMIT = 0x04
    PCD_TRANSCEIVE = 0x0C
    PCD_RESETPHASE = 0x0F
    PCD_CALCCRC = 0x03

    PICC_REQIDL = 0x26
    PICC_REQALL = 0x52
    PICC_ANTICOLL = 0x93
    PICC_SElECTTAG = 0x93
    PICC_AUTHENT1A = 0x60
    PICC_AUTHENT1B = 0x61
    PICC_READ = 0x30
    PICC_WRITE = 0xA0
    PICC_DECREMENT = 0xC0
    PICC_INCREMENT = 0xC1
    PICC_RESTORE = 0xC2
    PICC_TRANSFER = 0xB0
    PICC_HALT = 0x50

    MI_OK = 0
    MI_NOTAGERR = 1
    MI_ERR = 2

    # Register addresses
    CommandReg = 0x01
    CommIEnReg = 0x02
    CommIrqReg = 0x04
    ErrorReg = 0x06
    FIFODataReg = 0x09
    FIFOLevelReg = 0x0A
    ControlReg = 0x0C
    BitFramingReg = 0x0D
    ModeReg = 0x11
    TxControlReg = 0x14
    TxAutoReg = 0x15
    TModeReg = 0x2A
    TPrescalerReg = 0x2B
    TReloadRegL = 0x2C
    TReloadRegH = 0x2D
    VersionReg = 0x37

    def __init__(self, spi, cs):
        self.spi = spi
        self.cs = cs
        self.cs.value(1)
        self.MFRC522_Init()

    def MFRC522_Reset(self):
        self.Write_MFRC522(self.CommandReg, self.PCD_RESETPHASE)

    def Write_MFRC522(self, addr, val):
        self.cs.value(0)
        self.spi.write(bytes([(addr << 1) & 0x7E, val]))
        self.cs.value(1)

    def Read_MFRC522(self, addr):
        self.cs.value(0)
        self.spi.write(bytes([((addr << 1) & 0x7E) | 0x80]))
        val = self.spi.read(1)
        self.cs.value(1)
        return val[0]

    def SetBitMask(self, reg, mask):
        tmp = self.Read_MFRC522(reg)
        self.Write_MFRC522(reg, tmp | mask)

    def ClearBitMask(self, reg, mask):
        tmp = self.Read_MFRC522(reg)
        self.Write_MFRC522(reg, tmp & (~mask))

    def AntennaOn(self):
        temp = self.Read_MFRC522(self.TxControlReg)
        if(~(temp & 0x03)):
            self.SetBitMask(self.TxControlReg, 0x03)

    def MFRC522_ToCard(self, command, sendData):
        backData = []
        backLen = 0
        status = self.MI_ERR
        irqEn = 0x00
        waitIRq = 0x00

        if command == self.PCD_AUTHENT:
            irqEn = 0x12
            waitIRq = 0x10
        if command == self.PCD_TRANSCEIVE:
            irqEn = 0x77
            waitIRq = 0x30

        self.Write_MFRC522(self.CommIEnReg, irqEn | 0x80)
        self.ClearBitMask(self.CommIrqReg, 0x80)
        self.SetBitMask(self.FIFOLevelReg, 0x80)

        self.Write_MFRC522(self.CommandReg, self.PCD_IDLE)

        for i in range(len(sendData)):
            self.Write_MFRC522(self.FIFODataReg, sendData[i])

        self.Write_MFRC522(self.CommandReg, command)

        if command == self.PCD_TRANSCEIVE:
            self.SetBitMask(self.BitFramingReg, 0x80)

        i = 2000
        while True:
            n = self.Read_MFRC522(self.CommIrqReg)
            i = i - 1
            if ~((i != 0) and ~(n & 0x01) and ~(n & waitIRq)):
                break

        self.ClearBitMask(self.BitFramingReg, 0x80)

        if i != 0:
            if (self.Read_MFRC522(self.ErrorReg) & 0x1B) == 0x00:
                status = self.MI_OK

                if n & irqEn & 0x01:
                    status = self.MI_NOTAGERR

                if command == self.PCD_TRANSCEIVE:
                    n = self.Read_MFRC522(self.FIFOLevelReg)
                    lastBits = self.Read_MFRC522(self.ControlReg) & 0x07
                    if lastBits != 0:
                        backLen = (n - 1) * 8 + lastBits
                    else:
                        backLen = n * 8

                    if n == 0:
                        n = 1
                    if n > self.MAX_LEN:
                        n = self.MAX_LEN

                    for i in range(n):
                        backData.append(self.Read_MFRC522(self.FIFODataReg))

        return (status, backData, backLen)

    def MFRC522_Request(self, reqMode):
        status = None
        backBits = None
        TagType = []

        self.Write_MFRC522(self.BitFramingReg, 0x07)

        TagType.append(reqMode)
        (status, backData, backBits) = self.MFRC522_ToCard(self.PCD_TRANSCEIVE, TagType)

        if ((status != self.MI_OK) | (backBits != 0x10)):
            status = self.MI_ERR

        return (status, backBits)

    def MFRC522_Anticoll(self):
        backData = []
        serNumCheck = 0

        serNum = []

        self.Write_MFRC522(self.BitFramingReg, 0x00)

        serNum.append(self.PICC_ANTICOLL)
        serNum.append(0x20)

        (status, backData, backBits) = self.MFRC522_ToCard(self.PCD_TRANSCEIVE, serNum)

        if(status == self.MI_OK):
            i = 0
            if len(backData) == 5:
                for i in range(4):
                    serNumCheck = serNumCheck ^ backData[i]
                if serNumCheck != backData[4]:
                    status = self.MI_ERR
            else:
                status = self.MI_ERR

        return (status, backData)

    def MFRC522_Init(self):
        self.MFRC522_Reset()

        # Configure timer
        self.Write_MFRC522(self.TModeReg, 0x8D)        # Tauto=1; f(Timer) = 6.78MHz/TPreScaler
        self.Write_MFRC522(self.TPrescalerReg, 0x3E)   # TModeReg[3..0] + TPrescalerReg
        self.Write_MFRC522(self.TReloadRegL, 30)       
        self.Write_MFRC522(self.TReloadRegH, 0)

        # Configure modulation
        self.Write_MFRC522(self.TxAutoReg, 0x40)    # 100%ASK
        self.Write_MFRC522(self.ModeReg, 0x3D)      # CRC initial value 0x6363

        # Turn on the antenna
        self.AntennaOn()

class ReadPIRC522Client:
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
        
        # Initialize RC522 RFID reader
        sck = Pin(2, Pin.OUT)
        mosi = Pin(3, Pin.OUT)
        miso = Pin(0, Pin.IN)
        cs = Pin(1, Pin.OUT)
        
        # Set initial states
        cs.value(1)
        sck.value(0)
        
        # Initialize SPI for RC522
        spi = SPI(0,
                baudrate=1000000,  # 1MHz
                polarity=0,
                phase=0,
                bits=8,
                firstbit=SPI.MSB,
                sck=sck,
                mosi=mosi,
                miso=miso)
        
        self.rfid = MFRC522(spi, cs)
    
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
        self.display.text(font, "RC522 Edition", 40, 120, st7789.YELLOW)
    
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
    
    def format_uid(self, uid):
        """Format the UID as a hex string with colons between bytes"""
        return ':'.join(f'{x:02x}' for x in uid)
    
    def process_card(self, uid):
        """Process scanned RFID card"""
        card_id = self.format_uid(uid)
        current_time = time.time()
        
        # Check cooldown
        if card_id == self.last_card and (current_time - self.last_scan_time) < self.scan_cooldown:
            return
        
        self.last_card = card_id
        self.last_scan_time = current_time
        self.scan_count += 1
        
        print(f"Card scanned: {card_id} (Scan #{self.scan_count})")
        print(f"Available card mappings:")
        for k, v in self.card_assets.items():
            print(f"  {k} -> {v}")
        
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
            print("Card not found in mappings!")
            self.show_unknown_card(card_id)
    
    def run(self):
        """Main loop"""
        print("Starting ReadPI RC522 Exhibition Client...")
        
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
                # Check for cards
                (status, TagType) = self.rfid.MFRC522_Request(self.rfid.PICC_REQIDL)
                
                if status == self.rfid.MI_OK:
                    # Card detected, get UID
                    (status, uid) = self.rfid.MFRC522_Anticoll()
                    if status == self.rfid.MI_OK:
                        self.process_card(uid)
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("Client stopped")
            self.display.fill(0)
            self.display.text(font, "STOPPED", 60, 100, st7789.RED)

def main():
    client = ReadPIRC522Client()
    client.run()

if __name__ == "__main__":
    main() 