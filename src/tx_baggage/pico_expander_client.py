"""
Exhibition Client for Custom Pico Board with RC522
Simple RFID scanner that triggers videos and images on a remote server
Uses custom pico board with RC522 RFID reader and buzzer feedback

Pin Layout and Color Coding (Left Side Organization):

RC522 RFID Reader Connections:
- VCC/3.3V -> 3.3V [RED]     (Power)
- GND      -> GND  [BLACK]   (Ground)
- RST      -> GP5  [YELLOW]  (Reset pin)
- SDA/CS   -> GP1  [BLUE]    (SPI Chip Select)
- SCK      -> GP2  [GREEN]   (SPI Clock)
- MOSI     -> GP3  [ORANGE]  (SPI Master Out Slave In)
- MISO     -> GP0  [WHITE]   (SPI Master In Slave Out)

Feedback Components:
- LED      -> GP21 [PURPLE]  (Visual feedback)
- Buzzer   -> GP15 [BROWN]   (Audio feedback)
"""

import network
import urequests
import json
import time
from machine import Pin, SPI, PWM
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

    def __init__(self, spi, cs, rst=None):
        self.spi = spi
        self.cs = cs
        self.rst = rst
        self.cs.value(1)
        if self.rst:
            self.rst.value(1)
        self.MFRC522_Init()

    def MFRC522_Reset(self):
        if self.rst:
            self.rst.value(0)
            time.sleep(0.1)
            self.rst.value(1)
            time.sleep(0.1)
        self.Write_MFRC522(self.CommandReg, self.PCD_RESETPHASE)

    def Write_MFRC522(self, addr, val):
        self.cs.value(0)
        self.spi.write(bytes([(addr << 1) & 0x7E, val]))
        self.cs.value(1)

    def Read_MFRC522(self, addr):
        self.cs.value(0)
        self.spi.write(bytes([((addr << 1) & 0x7E) | 0x80]))
        result = self.spi.read(1)
        self.cs.value(1)
        return result[0]

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

class ExhibitionClientPico:
    def __init__(self):
        # Configuration from config.py
        self.WIFI_SSID = config.WIFI_SSID
        self.WIFI_PASSWORD = config.WIFI_PASSWORD
        self.SERVER_IP = config.SERVER_IP
        self.SERVER_PORT = config.SERVER_PORT
        self.card_assets = config.CARD_ASSETS
        
        # Hardware Setup
        self.setup_hardware()
        
        # State management
        self.wifi_connected = False
        self.last_card = None
        self.last_scan_time = 0
        self.scan_cooldown = 3.0
        self.scan_count = 0
        
        # Card presence tracking to prevent repeated scans
        self.card_present = False
        self.no_card_count = 0
        self.current_card_processed = False
        self.card_removal_threshold = 20  # Failed reads before considering card removed
    
    def setup_hardware(self):
        """Initialize hardware components"""
        # Initialize LEDs
        self.led = Pin(21, Pin.OUT)  # External LED
        self.onboard_led = Pin("LED", Pin.OUT)  # Built-in Pico W LED
        
        # Initialize buzzer
        self.buzzer = PWM(Pin(15))
        self.buzzer.duty_u16(0)
        
        # Initialize RC522 RFID reader
        sck = Pin(2, Pin.OUT)
        mosi = Pin(3, Pin.OUT)
        miso = Pin(0, Pin.IN)
        cs = Pin(1, Pin.OUT)
        rst = Pin(5, Pin.OUT)
        
        # Set initial states
        cs.value(1)
        sck.value(0)
        rst.value(1)
        
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
        
        self.rfid = MFRC522(spi, cs, rst)
        
        print("Hardware initialized!")
        print("RC522 RFID Reader ready")
        print("LEDs and buzzer ready")
    
    def beep(self, frequency=1000, duration=0.1):
        """Play a beep sound"""
        self.buzzer.duty_u16(5000)
        self.buzzer.freq(frequency)
        time.sleep(duration)
        self.buzzer.duty_u16(0)
    
    def success_feedback(self):
        """Provide success feedback with LEDs and buzzer"""
        # LED pattern: quick flash for both LEDs
        for _ in range(3):
            self.led.on()
            self.onboard_led.on()
            time.sleep(0.1)
            self.led.off()
            self.onboard_led.off()
            time.sleep(0.1)
        
        # Buzzer: success tone sequence
        for freq in [1000, 1200, 1500]:
            self.beep(freq, 0.1)
    
    def error_feedback(self):
        """Provide error feedback with LEDs and buzzer"""
        # LED pattern: long flash for both LEDs
        self.led.on()
        self.onboard_led.on()
        time.sleep(0.5)
        self.led.off()
        self.onboard_led.off()
        
        # Buzzer: error tone
        self.beep(500, 0.3)
    
    def connect_wifi(self):
        """Fast WiFi connection with fallback for UPS/battery power"""
        print("Connecting to WiFi...")
        
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        
        # FAST PATH: Try quick connection first (works when USB powered or good conditions)
        print("Trying fast connection...")
        if not wlan.isconnected():
            wlan.connect(self.WIFI_SSID, self.WIFI_PASSWORD)
            
            # Quick timeout - only 8 seconds
            timeout = 16  # 8 seconds total
            while not wlan.isconnected() and timeout > 0:
                self.onboard_led.toggle()
                time.sleep(0.5)
                timeout -= 1
        
        if wlan.isconnected():
            self.wifi_connected = True
            ip = wlan.ifconfig()[0]
            print(f"WiFi Connected Fast! IP: {ip}")
            self.beep(1000, 0.1)
            return True
        
        # ROBUST PATH: If fast connection failed, use robust method
        print("Fast connection failed, trying robust method...")
        print("Power stabilization delay...")
        time.sleep(1)  # Reduced from 2 seconds
        
        # Reset WiFi for clean state
        wlan.active(False)
        time.sleep(0.5)  # Reduced delay
        wlan.active(True)
        time.sleep(0.5)  # Reduced delay
        
        # Try 2 attempts with shorter timeouts
        max_retries = 2  # Reduced from 3
        for attempt in range(max_retries):
            print(f"Robust attempt {attempt + 1}/{max_retries}")
            
            wlan.connect(self.WIFI_SSID, self.WIFI_PASSWORD)
            
            # Shorter timeout for robust attempts
            timeout = 24  # 12 seconds total
            while not wlan.isconnected() and timeout > 0:
                self.onboard_led.toggle()
                time.sleep(0.5)
                timeout -= 1
                
                # Show progress less frequently
                if timeout % 6 == 0:
                    print(f"Waiting... {timeout//2}s left")
            
            if wlan.isconnected():
                self.wifi_connected = True
                ip = wlan.ifconfig()[0]
                print(f"WiFi Connected! IP: {ip}")
                self.beep(1000, 0.1)
                return True
            else:
                print(f"Robust attempt {attempt + 1} failed")
                if attempt < max_retries - 1:
                    print("Quick retry...")
                    time.sleep(1)  # Reduced from 3 seconds
                    wlan.active(False)
                    time.sleep(0.5)
                    wlan.active(True)
                    time.sleep(0.5)
        
        print("All WiFi connection attempts failed!")
        self.error_feedback()
        return False
    
    def test_server(self):
        """Test connection to asset server"""
        try:
            print("Testing server connection...")
            url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/ping"
            print(f"Testing server at: {url}")
            response = urequests.get(url, timeout=5)
            
            if response.status_code == 200:
                print("Server connection OK!")
                self.beep(1200, 0.1)
                response.close()
                return True
            else:
                raise Exception(f"Server error: {response.status_code}")
                
        except Exception as e:
            print(f"Server test failed: {e}")
            print(f"Make sure asset server is running at {self.SERVER_IP}:{self.SERVER_PORT}")
            self.error_feedback()
            return False
    
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
    
    def trigger_unknown_card(self, card_id):
        """Send unknown card information to server for tracking"""
        try:
            url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/unknown-card"
            data = {
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
            if success:
                print(f"Unknown card {card_id} logged to server")
            response.close()
            return success
            
        except Exception as e:
            print(f"Failed to log unknown card: {e}")
            return False
    
    def format_uid(self, uid):
        """Format the UID as a hex string with colons between bytes"""
        return ':'.join(f'{x:02x}' for x in uid)
    
    def process_card(self, uid):
        """Process scanned RFID card with duplicate prevention"""
        card_id = self.format_uid(uid)
        current_time = time.time()
        
        # Prevent processing the same card multiple times while it sits on scanner
        if card_id == self.last_card and self.card_present and self.current_card_processed:
            return
        
        # Enforce cooldown period for the same card
        if card_id == self.last_card and (current_time - self.last_scan_time) < self.scan_cooldown:
            self.card_present = True  # Update presence but don't process
            return
        
        # Process the card
        self.last_card = card_id
        self.last_scan_time = current_time
        self.scan_count += 1
        self.card_present = True
        self.current_card_processed = True
        self.no_card_count = 0
        
        print(f"\nCard scanned: {card_id} (Scan #{self.scan_count})")
        
        # Visual feedback - turn on LEDs
        self.led.on()
        self.onboard_led.on()
        
        asset_file = self.card_assets.get(card_id)
        
        if asset_file:
            print(f"Triggering asset: {asset_file}")
            if self.trigger_asset(card_id, asset_file):
                print("Asset triggered successfully!")
                self.success_feedback()
            else:
                print("Failed to trigger asset")
                self.error_feedback()
        else:
            print(f"Unknown card: {card_id}")
            print("Card not found in mappings!")
            self.error_feedback()
            
            if self.trigger_unknown_card(card_id):
                print("Unknown card logged to server")
            else:
                print("Failed to log unknown card")
        
        # Turn off LEDs
        self.led.off()
        self.onboard_led.off()
    
    def run(self):
        """Main loop"""
        print("Starting Exhibition Client for Custom Pico Board...")
        print("Pin connections:")
        print("RC522: RST=GP5, CS=GP1, SCK=GP2, MOSI=GP3, MISO=GP0")
        print("LED: GP21, Buzzer: GP15")
        
        if not self.connect_wifi():
            print("WiFi connection failed!")
            return
        
        if not self.test_server():
            print("Server connection failed!")
        
        print("\nReady to scan RFID cards!")
        print("Mapped assets:")
        for card_id, asset_file in self.card_assets.items():
            print(f"  {card_id} -> {asset_file}")
        print(f"Scan cooldown: {self.scan_cooldown} seconds")
        
        # Ready indication
        self.beep(800, 0.2)
        time.sleep(0.1)
        self.beep(1000, 0.2)
        
        try:
            while True:
                # Check for cards
                (status, TagType) = self.rfid.MFRC522_Request(self.rfid.PICC_REQIDL)
                
                if status == self.rfid.MI_OK:
                    # Card detected, get UID
                    (status, uid) = self.rfid.MFRC522_Anticoll()
                    if status == self.rfid.MI_OK:
                        self.process_card(uid)
                        self.no_card_count = 0  # Reset no-card counter
                    else:
                        # Card detection failed
                        self.no_card_count += 1
                else:
                    # No card detected
                    self.no_card_count += 1
                
                # If we haven't detected a card for several consecutive reads,
                # consider the card removed
                if self.no_card_count >= self.card_removal_threshold and self.card_present:
                    self.card_present = False
                    self.current_card_processed = False  # Reset processed flag when card is removed
                    # Don't reset last_card - keep it for cooldown purposes
                    print("Card removed from scanner")
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\nClient stopped")
            self.led.off()
            self.onboard_led.off()
            self.buzzer.duty_u16(0)

def main():
    client = ExhibitionClientPico()
    client.run()

if __name__ == "__main__":
    main() 