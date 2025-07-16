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
import gc  # Garbage collection for memory management
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
            time.sleep(0.05)  # Reduced from 0.1s
            self.rst.value(1)
            time.sleep(0.05)  # Reduced from 0.1s
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

        # Reduced timeout for faster response
        i = 1500  # Reduced from 2000
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
        
        # Optimized state management
        self.wifi_connected = False
        self.current_card = None
        self.card_present = False
        self.card_processed = False  # Track if current card has been processed
        self.last_process_time = 0
        self.process_cooldown = 1.0  # Reduced from 1.5 seconds
        
        # Simplified card detection
        self.consecutive_detections = 0
        self.consecutive_failures = 0
        
        # Performance constants
        self.DETECTION_THRESHOLD = 2  # Reduced from 3
        self.REMOVAL_THRESHOLD = 15   # Much higher threshold for stable removal detection
        
        # Performance monitoring
        self.scan_count = 0
        self.start_time = time.time()
        self.last_stats_time = time.time()
        
        # Memory management
        self.gc_counter = 0
        self.GC_INTERVAL = 100  # Run GC every 100 scans
    
    def setup_hardware(self):
        """Initialize hardware components with optimized settings"""
        # Initialize LEDs
        self.led = Pin(21, Pin.OUT)  # External LED
        self.onboard_led = Pin("LED", Pin.OUT)  # Built-in Pico W LED
        
        # Initialize buzzer
        self.buzzer = PWM(Pin(15))
        self.buzzer.duty_u16(0)
        
        # Initialize RC522 RFID reader with optimized SPI settings
        sck = Pin(2, Pin.OUT)
        mosi = Pin(3, Pin.OUT)
        miso = Pin(0, Pin.IN)
        cs = Pin(1, Pin.OUT)
        rst = Pin(5, Pin.OUT)
        
        # Set initial states
        cs.value(1)
        sck.value(0)
        rst.value(1)
        
        # Initialize SPI with higher baudrate for better performance
        spi = SPI(0,
                baudrate=2000000,  # Increased from 1MHz to 2MHz
                polarity=0,
                phase=0,
                bits=8,
                firstbit=SPI.MSB,
                sck=sck,
                mosi=mosi,
                miso=miso)
        
        self.rfid = MFRC522(spi, cs, rst)
        
        print("Hardware initialized with performance optimizations!")
        print("RC522 RFID Reader ready (2MHz SPI)")
        print("LEDs and buzzer ready")
    
    def beep(self, frequency=1000, duration=0.15):  # Restored reasonable duration
        """Play a beep sound"""
        self.buzzer.duty_u16(5000)
        self.buzzer.freq(frequency)
        time.sleep(duration)
        self.buzzer.duty_u16(0)
    
    def success_feedback(self):
        """Provide optimized success feedback"""
        # Faster LED pattern
        for _ in range(2):  # Reduced from 3
            self.led.on()
            self.onboard_led.on()
            time.sleep(0.05)  # Reduced from 0.1
            self.led.off()
            self.onboard_led.off()
            time.sleep(0.05)
        
        # Pleasant success tone
        self.beep(1200, 0.2)
    
    def error_feedback(self):
        """Provide optimized error feedback"""
        # Shorter LED flash
        self.led.on()
        self.onboard_led.on()
        time.sleep(0.2)  # Reduced from 0.5
        self.led.off()
        self.onboard_led.off()
        
        # Clear error tone
        self.beep(500, 0.25)  # Longer for better error indication
    
    def connect_wifi(self):
        """Optimized WiFi connection"""
        print("Connecting to WiFi...")
        
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        
        # FAST PATH: Try quick connection first
        print("Trying fast connection...")
        if not wlan.isconnected():
            wlan.connect(self.WIFI_SSID, self.WIFI_PASSWORD)
            
            # Reduced timeout
            timeout = 12  # 6 seconds total
            while not wlan.isconnected() and timeout > 0:
                self.onboard_led.toggle()
                time.sleep(0.5)
                timeout -= 1
        
        if wlan.isconnected():
            self.wifi_connected = True
            ip = wlan.ifconfig()[0]
            print(f"WiFi Connected Fast! IP: {ip}")
            self.beep(1000, 0.15)
            return True
        
        # ROBUST PATH: Simplified robust method
        print("Fast connection failed, trying robust method...")
        time.sleep(0.5)  # Reduced stabilization delay
        
        # Reset WiFi
        wlan.active(False)
        time.sleep(0.3)
        wlan.active(True)
        time.sleep(0.3)
        
        # Single robust attempt with shorter timeout
        print("Robust connection attempt...")
        wlan.connect(self.WIFI_SSID, self.WIFI_PASSWORD)
        
        timeout = 16  # 8 seconds total
        while not wlan.isconnected() and timeout > 0:
            self.onboard_led.toggle()
            time.sleep(0.5)
            timeout -= 1
        
        if wlan.isconnected():
            self.wifi_connected = True
            ip = wlan.ifconfig()[0]
            print(f"WiFi Connected! IP: {ip}")
            self.beep(1000, 0.15)
            return True
        
        print("WiFi connection failed!")
        self.error_feedback()
        return False
    
    def test_server(self):
        """Test server connection with shorter timeout"""
        try:
            print("Testing server connection...")
            url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/ping"
            response = urequests.get(url, timeout=3)  # Reduced from 5s
            
            if response.status_code == 200:
                print("Server connection OK!")
                self.beep(1200, 0.15)
                response.close()
                return True
            else:
                raise Exception(f"Server error: {response.status_code}")
                
        except Exception as e:
            print(f"Server test failed: {e}")
            self.error_feedback()
            return False
    
    def trigger_card_assets(self, card_id):
        """Optimized card trigger with shorter timeout and better memory management"""
        response = None
        try:
            url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/play"
            data = {
                "card_id": card_id,
                "timestamp": time.time()
            }
            
            response = urequests.post(
                url, 
                data=json.dumps(data),
                headers={'Content-Type': 'application/json'},
                timeout=5  # Reduced from 10s
            )
            
            success = response.status_code == 200
            if success:
                # Parse response efficiently
                try:
                    response_data = response.json()
                    asset_file = response_data.get('asset_file', 'Unknown')
                    asset_index = response_data.get('asset_index', 0)
                    total_assets = response_data.get('total_assets', 1)
                    print(f"Asset: {asset_file} ({asset_index + 1}/{total_assets})")
                except:
                    pass
            
            return success
            
        except Exception as e:
            print(f"Failed to trigger card assets: {e}")
            return False
        finally:
            if response:
                response.close()
            # Force garbage collection after network operation
            gc.collect()
    
    def trigger_unknown_card(self, card_id):
        """Optimized unknown card logging"""
        response = None
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
                timeout=3  # Reduced timeout
            )
            
            success = response.status_code == 200
            if success:
                print(f"Unknown card {card_id} logged")
            return success
            
        except Exception as e:
            print(f"Failed to log unknown card: {e}")
            return False
        finally:
            if response:
                response.close()
            gc.collect()
    
    def trigger_card_removal(self, card_id):
        """Optimized card removal signal"""
        response = None
        try:
            url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/card-removed"
            data = {
                "card_id": card_id,
                "timestamp": time.time()
            }
            
            response = urequests.post(
                url, 
                data=json.dumps(data),
                headers={'Content-Type': 'application/json'},
                timeout=3  # Reduced timeout
            )
            
            success = response.status_code == 200
            if success:
                print(f"Card {card_id} removal signaled")
            return success
            
        except Exception as e:
            print(f"Failed to signal card removal: {e}")
            return False
        finally:
            if response:
                response.close()
            gc.collect()
    
    def format_uid(self, uid):
        """Format the UID as a hex string with colons between bytes"""
        return ':'.join(f'{x:02x}' for x in uid)
    
    def process_card(self, card_id):
        """Optimized card processing with simplified state management"""
        # Process the card (cooldown logic is handled in main loop)
        self.current_card = card_id
        self.last_process_time = time.time()
        self.scan_count += 1
        
        print(f"Card: {card_id} (#{self.scan_count})")
        
        # Quick LED feedback
        self.led.on()
        self.onboard_led.on()
        
        # Check card mapping
        card_mapping = self.card_assets.get(card_id)
        
        if card_mapping:
            # Mapped card
            if self.trigger_card_assets(card_id):
                self.success_feedback()
            else:
                self.error_feedback()
        else:
            # Unknown card
            print(f"Unknown: {card_id}")
            self.error_feedback()
            self.trigger_unknown_card(card_id)
        
        # Turn off LEDs
        self.led.off()
        self.onboard_led.off()
        
        return True
    
    def print_performance_stats(self):
        """Print performance statistics"""
        current_time = time.time()
        if current_time - self.last_stats_time > 30:  # Every 30 seconds
            elapsed = current_time - self.start_time
            if elapsed > 0:
                scan_rate = self.scan_count / elapsed
                print(f"Performance: {scan_rate:.1f} scans/sec, {self.scan_count} total scans")
                print(f"Memory free: {gc.mem_free()} bytes")
            self.last_stats_time = current_time
    
    def run(self):
        """Optimized main loop"""
        print("Starting Performance-Optimized Exhibition Client...")
        print("Performance improvements:")
        print("- Faster SPI (2MHz)")
        print("- Reduced delays and timeouts")
        print("- Optimized card detection")
        print("- Better memory management")
        print("Created by Marcus Chan")
        
        if not self.connect_wifi():
            print("WiFi connection failed!")
            return
        
        if not self.test_server():
            print("Server connection failed!")
        
        print(f"\nReady! Mapped cards: {len(self.card_assets)}")
        print(f"Cooldown: {self.process_cooldown}s")
        
        # Ready indication
        self.beep(800, 0.2)
        time.sleep(0.1)
        self.beep(1000, 0.2)
        
        try:
            scan_counter = 0
            while True:
                scan_counter += 1
                
                # Check for cards
                (status, TagType) = self.rfid.MFRC522_Request(self.rfid.PICC_REQIDL)
                
                if status == self.rfid.MI_OK:
                    # Card detected, get UID
                    (status, uid) = self.rfid.MFRC522_Anticoll()
                    if status == self.rfid.MI_OK:
                        # Successful detection
                        self.consecutive_detections += 1
                        self.consecutive_failures = 0
                        
                        # Process card with strict duplicate prevention
                        card_id = self.format_uid(uid)
                        
                        # Only process if it's a genuinely new card or hasn't been processed yet
                        should_process = False
                        current_time = time.time()
                        
                        if card_id != self.current_card:
                            # Different card, always process
                            should_process = True
                        elif not self.card_processed:
                            # Same card but not processed yet, process it
                            should_process = True
                        # If same card and already processed, do NOT process again
                        
                        if should_process:
                            self.card_present = True
                            self.process_card(card_id)
                            self.card_processed = True  # Mark as processed

                    else:
                        # Failed UID read
                        self.consecutive_failures += 1
                        self.consecutive_detections = 0
                else:
                    # No card detected
                    self.consecutive_failures += 1
                    self.consecutive_detections = 0
                
                # Check for card removal
                if self.consecutive_failures >= self.REMOVAL_THRESHOLD and self.card_present:
                    self.card_present = False
                    self.card_processed = False  # Reset processed flag
                    if self.current_card:
                        self.trigger_card_removal(self.current_card)
                        print("Card removed")
                        # Keep current_card for potential re-placement detection
                
                # Memory management
                self.gc_counter += 1
                if self.gc_counter >= self.GC_INTERVAL:
                    gc.collect()
                    self.gc_counter = 0
                
                # Performance monitoring
                if scan_counter % 300 == 0:  # Every 300 scans
                    self.print_performance_stats()
                
                # Optimized loop delay
                time.sleep(0.03)  # Reduced from 0.1s to 0.03s for 33% faster scanning
                
        except KeyboardInterrupt:
            print("\nClient stopped")
            print(f"Final stats: {self.scan_count} scans processed")
            self.led.off()
            self.onboard_led.off()
            self.buzzer.duty_u16(0)

def main():
    client = ExhibitionClientPico()
    client.run()

if __name__ == "__main__":
    main() 