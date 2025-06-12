"""
RC522 RFID Reader Implementation for Pico Dual Expander Board
This program demonstrates RFID card reading with visual and audio feedback.

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
- LED      -> GP21 [PURPLE]  (Visual feedback - already on board)
- Buzzer   -> GP15 [BROWN]   (Audio feedback - optional)
"""

from machine import Pin, SPI, PWM
import time

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

    Reserved00 = 0x00
    CommandReg = 0x01
    CommIEnReg = 0x02
    DivlEnReg = 0x03
    CommIrqReg = 0x04
    DivIrqReg = 0x05
    ErrorReg = 0x06
    Status1Reg = 0x07
    Status2Reg = 0x08
    FIFODataReg = 0x09
    FIFOLevelReg = 0x0A
    WaterLevelReg = 0x0B
    ControlReg = 0x0C
    BitFramingReg = 0x0D
    CollReg = 0x0E
    Reserved01 = 0x0F

    Reserved10 = 0x10
    ModeReg = 0x11
    TxModeReg = 0x12
    RxModeReg = 0x13
    TxControlReg = 0x14
    TxAutoReg = 0x15
    TxSelReg = 0x16
    RxSelReg = 0x17
    RxThresholdReg = 0x18
    DemodReg = 0x19
    Reserved11 = 0x1A
    Reserved12 = 0x1B
    MifareReg = 0x1C
    Reserved13 = 0x1D
    Reserved14 = 0x1E
    SerialSpeedReg = 0x1F

    Reserved20 = 0x20
    CRCResultRegM = 0x21
    CRCResultRegL = 0x22
    Reserved21 = 0x23
    ModWidthReg = 0x24
    Reserved22 = 0x25
    RFCfgReg = 0x26
    GsNReg = 0x27
    CWGsPReg = 0x28
    ModGsPReg = 0x29
    TModeReg = 0x2A
    TPrescalerReg = 0x2B
    TReloadRegH = 0x2C
    TReloadRegL = 0x2D
    TCounterValueRegH = 0x2E
    TCounterValueRegL = 0x2F

    Reserved30 = 0x30
    TestSel1Reg = 0x31
    TestSel2Reg = 0x32
    TestPinEnReg = 0x33
    TestPinValueReg = 0x34
    TestBusReg = 0x35
    AutoTestReg = 0x36
    VersionReg = 0x37
    AnalogTestReg = 0x38
    TestDAC1Reg = 0x39
    TestDAC2Reg = 0x3A
    TestADCReg = 0x3B
    Reserved31 = 0x3C
    Reserved32 = 0x3D
    Reserved33 = 0x3E
    Reserved34 = 0x3F

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

    def AntennaOff(self):
        self.ClearBitMask(self.TxControlReg, 0x03)

    def MFRC522_ToCard(self, command, sendData):
        backData = []
        backLen = 0
        status = self.MI_ERR
        irqEn = 0x00
        waitIRq = 0x00
        lastBits = None
        n = 0

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
            else:
                status = self.MI_ERR

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

    def CalulateCRC(self, pIndata):
        self.ClearBitMask(self.DivIrqReg, 0x04)
        self.SetBitMask(self.FIFOLevelReg, 0x80)

        for i in range(len(pIndata)):
            self.Write_MFRC522(self.FIFODataReg, pIndata[i])

        self.Write_MFRC522(self.CommandReg, self.PCD_CALCCRC)
        i = 0xFF
        while True:
            n = self.Read_MFRC522(self.DivIrqReg)
            i = i - 1
            if not ((i != 0) and not (n & 0x04)):
                break
        pOutData = []
        pOutData.append(self.Read_MFRC522(self.CRCResultRegL))
        pOutData.append(self.Read_MFRC522(self.CRCResultRegM))
        return pOutData

    def MFRC522_Init(self):
        self.MFRC522_Reset()
        
        # Add version check
        version = self.Read_MFRC522(self.VersionReg)
        print(f"MFRC522 Version: 0x{version:02x}")
        
        # Update version check to include 0x82
        if version not in [0x91, 0x92, 0x82]:
            print("Warning: Unknown MFRC522 version or communication error!")
        else:
            print("Valid MFRC522 version detected")

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
        print("MFRC522 Initialized")

class PicoExpanderRFID:
    def __init__(self):
        # Initialize feedback components
        self.led = Pin(21, Pin.OUT)  # External LED
        self.onboard_led = Pin("LED", Pin.OUT)  # Built-in Pico W LED
        
        # Initialize buzzer (optional)
        try:
            self.buzzer = PWM(Pin(15))
            self.buzzer.duty_u16(0)
            self.has_buzzer = True
        except:
            self.has_buzzer = False
            print("Buzzer not available on GP15")
        
        print("Pico Expander RFID Reader initialized!")
        print("\nComponent Connections:")
        print("RC522 RFID Reader:")
        print("- VCC/3.3V -> 3.3V [RED]")
        print("- GND      -> GND  [BLACK]")
        print("- RST      -> GP5  [YELLOW]")
        print("- SDA/CS   -> GP1  [BLUE]")
        print("- SCK      -> GP2  [GREEN]")
        print("- MOSI     -> GP3  [ORANGE]")
        print("- MISO     -> GP0  [WHITE]")
        print("\nFeedback:")
        print("- External LED -> GP21 [PURPLE]")
        print("- Built-in LED -> Pico W onboard LED")
        if self.has_buzzer:
            print("- Buzzer   -> GP15 [BROWN]")
    
    def beep(self, frequency=1000, duration=0.1):
        """Play a beep sound if buzzer is available"""
        if self.has_buzzer:
            self.buzzer.duty_u16(5000)
            self.buzzer.freq(frequency)
            time.sleep(duration)
            self.buzzer.duty_u16(0)
    
    def success_feedback(self):
        """Provide success feedback with LEDs and optional buzzer"""
        # LED pattern: quick flash for both LEDs
        for _ in range(3):
            self.led.on()
            self.onboard_led.on()
            time.sleep(0.1)
            self.led.off()
            self.onboard_led.off()
            time.sleep(0.1)
        
        # Buzzer: success tone
        if self.has_buzzer:
            self.beep(1000, 0.1)
            time.sleep(0.05)
            self.beep(1500, 0.1)
    
    def error_feedback(self):
        """Provide error feedback with LEDs and optional buzzer"""
        # LED pattern: long flash for both LEDs
        self.led.on()
        self.onboard_led.on()
        time.sleep(0.5)
        self.led.off()
        self.onboard_led.off()
        
        # Buzzer: error tone
        if self.has_buzzer:
            self.beep(500, 0.3)

# Main program
def main():
    print("Initializing Pico Expander RFID System...")
    
    # Initialize feedback system
    feedback = PicoExpanderRFID()
    
    print("\nInitializing SPI...")
    try:
        # Initialize pins first
        sck = Pin(2, Pin.OUT)
        mosi = Pin(3, Pin.OUT)
        miso = Pin(0, Pin.IN)
        cs = Pin(1, Pin.OUT)
        rst = Pin(5, Pin.OUT)
        
        # Set initial states
        cs.value(1)  # CS must be high initially
        sck.value(0)  # Clock low initially
        rst.value(1)  # RST high initially
        
        # Initialize SPI with lower baudrate and mode 0
        spi = SPI(0,
                baudrate=1000000,  # 1MHz
                polarity=0,
                phase=0,
                bits=8,
                firstbit=SPI.MSB,
                sck=sck,
                mosi=mosi,
                miso=miso)
        
        print("SPI initialized successfully")
        print("Testing SPI communication...")
        
        # Initialize RC522 RFID reader
        print("Initializing MFRC522...")
        rfid = MFRC522(spi, cs, rst)
        
        # Read version register multiple times to ensure communication
        versions = []
        for i in range(3):
            version = rfid.Read_MFRC522(rfid.VersionReg)
            versions.append(version)
            print(f"MFRC522 Version Read {i+1}: 0x{version:02x}")
            time.sleep(0.1)
            
        if len(set(versions)) != 1 or versions[0] in [0x00, 0xFF]:
            print("\nDiagnostic Information:")
            print("- Inconsistent or invalid version readings")
            print("Please check connections according to color coding:")
            print("  VCC/3.3V -> 3.3V [RED]")
            print("  GND      -> GND  [BLACK]")
            print("  RST      -> GP5  [YELLOW]")
            print("  SDA/CS   -> GP1  [BLUE]")
            print("  SCK      -> GP2  [GREEN]")
            print("  MOSI     -> GP3  [ORANGE]")
            print("  MISO     -> GP0  [WHITE]")
            feedback.error_feedback()
            return
        
        # Success feedback for initialization
        feedback.success_feedback()
        
        print("\nPico Expander RC522 RFID Reader Ready!")
        print("Place an RFID card near the reader...")
        print("(LED will flash and buzzer will beep when a card is detected)")
        
        last_read_time = 0
        
        while True:
            try:
                # Check for cards
                (status, TagType) = rfid.MFRC522_Request(rfid.PICC_REQIDL)
                
                if status == rfid.MI_OK:
                    current_time = time.time()
                    # Only process if it's been at least 1 second since last read
                    if current_time - last_read_time >= 1:
                        print("\nCard detected!")
                        feedback.led.on()
                        feedback.onboard_led.on()
                        
                        # Get the UID of the card
                        (status, uid) = rfid.MFRC522_Anticoll()
                        
                        if status == rfid.MI_OK:
                            # Print the UID
                            print("Card UID: ", end="")
                            uid_str = ""
                            for i in range(0, len(uid)-1):
                                uid_str += f"{uid[i]:02x}:"
                                print(f"{uid[i]:02x}", end=":")
                            uid_str += f"{uid[-1]:02x}"
                            print(f"{uid[-1]:02x}")
                            
                            last_read_time = current_time
                            
                            # Success feedback
                            feedback.success_feedback()
                        else:
                            print("Error reading card UID")
                            feedback.error_feedback()
                        
                        feedback.led.off()
                        feedback.onboard_led.off()
                
            except Exception as e:
                print(f"Error during card reading: {e}")
                feedback.error_feedback()
                time.sleep(1)
            
            time.sleep(0.1)
            
    except Exception as e:
        print(f"Initialization error: {e}")
        if 'feedback' in locals():
            feedback.error_feedback()
        
if __name__ == "__main__":
    main() l