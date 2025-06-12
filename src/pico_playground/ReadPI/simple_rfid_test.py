# Simplified RFID Test - No Display Required
from machine import UART, Pin, PWM
import time

# Setup buzzer
buzzer = PWM(Pin(15))

def playtone(frequency):
    buzzer.duty_u16(5000)
    buzzer.freq(frequency)

def bequiet():
    buzzer.duty_u16(0)

# Setup UART for RFID (GP4=RX, GP5=TX)
uart = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))

# Setup onboard LED for indication
led = Pin("LED", Pin.OUT)

print("PicoRFID RFID Test Starting...")
print("Place an RFID card near the reader...")
print("Waiting for RFID cards...")

bequiet()

while True:
    # Check if data is available from RFID module
    if uart.any():
        # Read available data
        data = uart.read()
        if data:
            try:
                # Decode and print the card data
                card_id = data.decode("utf-8").strip()
                print(f"Card detected: {card_id}")
                
                # Visual and audio feedback
                led.on()
                playtone(1865)
                time.sleep(0.2)
                bequiet()
                led.off()
                
            except:
                print(f"Raw data received: {data}")
                led.on()
                playtone(1000)
                time.sleep(0.1)
                bequiet()
                led.off()
    
    time.sleep(0.1) 