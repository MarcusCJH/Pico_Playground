"""
ReadPi Complete Demo - All Capabilities in One File
====================================================

This is a simple demonstration that shows everything the ReadPi can do:
- LED control and patterns
- Buzzer sounds and melodies  
- Display text, colors, and graphics
- Joystick input detection
- RFID card reading
- WiFi connectivity
- System information

Just copy this file as main.py to your ReadPi and it will run automatically!

Hardware: ReadPi RFID Reader (125KHz) with Raspberry Pi Pico W
"""

from machine import Pin, SPI, UART, PWM, unique_id
import time
import network
import gc
import st7789
import vga1_bold_16x32 as font

# ===== HARDWARE SETUP =====
# Display (1.3" IPS 240x240)
spi = SPI(1, baudrate=40000000, sck=Pin(10), mosi=Pin(11))
display = st7789.ST7789(spi, 240, 240, reset=Pin(12, Pin.OUT), 
                       cs=Pin(9, Pin.OUT), dc=Pin(8, Pin.OUT), 
                       backlight=Pin(13, Pin.OUT), rotation=1)

# RFID Reader (125KHz) - Handle potential pin conflicts
rfid = None
rfid_available = False
try:
    # Try different UART configurations
    rfid = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))
    rfid_available = True
    print("RFID: Using GP4(TX), GP5(RX)")
except:
    try:
        rfid = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))
        rfid_available = True
        print("RFID: Using GP0(TX), GP1(RX)")
    except:
        print("RFID: Not available (pin conflict)")
        rfid_available = False

# Audio & Visual Feedback
buzzer = PWM(Pin(15))
led = Pin("LED", Pin.OUT)

# 5-Way Joystick
joy_up = Pin(22, Pin.IN, Pin.PULL_UP)
joy_down = Pin(26, Pin.IN, Pin.PULL_UP)
joy_left = Pin(21, Pin.IN, Pin.PULL_UP)
joy_right = Pin(14, Pin.IN, Pin.PULL_UP)
joy_select = Pin(27, Pin.IN, Pin.PULL_UP)

# WiFi
wlan = network.WLAN(network.STA_IF)

# Demo state
demo_step = 0
cards_read = 0
start_time = time.time()

# ===== HELPER FUNCTIONS =====
def beep(freq=1000, duration=0.2):
    """Play a beep sound"""
    buzzer.duty_u16(3000)
    buzzer.freq(freq)
    time.sleep(duration)
    buzzer.duty_u16(0)

def show_text(text, color=st7789.WHITE, clear=True):
    """Display text on screen"""
    if clear:
        display.fill(st7789.BLACK)
    
    lines = text.split('\n')
    for i, line in enumerate(lines):
        y = 40 + (i * 25)
        if y < 240:
            display.text(font, line, 10, y, color)

def read_joystick():
    """Check if any joystick button is pressed"""
    return (not joy_up.value() or not joy_down.value() or 
            not joy_left.value() or not joy_right.value() or 
            not joy_select.value())

def startup_melody():
    """Play a welcome melody"""
    notes = [523, 659, 784, 1047]  # C, E, G, C
    for note in notes:
        beep(note, 0.15)
        time.sleep(0.05)

# ===== DEMO FUNCTIONS =====
def demo_welcome():
    """Welcome screen and startup"""
    display.init()
    display.fill(st7789.BLACK)
    
    # Title
    display.text(font, "ReadPi Demo", 50, 80, st7789.CYAN)
    display.text(font, "Loading...", 70, 120, st7789.WHITE)
    
    startup_melody()
    time.sleep(2)

def demo_display():
    """Demonstrate display capabilities"""
    show_text("DISPLAY TEST\n\nColors & Graphics", st7789.CYAN)
    time.sleep(2)
    
    # Color test
    colors = [(st7789.RED, "RED"), (st7789.GREEN, "GREEN"), 
              (st7789.BLUE, "BLUE"), (st7789.YELLOW, "YELLOW")]
    
    for color, name in colors:
        display.fill(color)
        text_color = st7789.BLACK if color == st7789.YELLOW else st7789.WHITE
        display.text(font, name, 80, 100, text_color)
        time.sleep(0.8)
    
    # Graphics test
    display.fill(st7789.BLACK)
    display.text(font, "Graphics Test", 40, 10, st7789.WHITE)
    
    # Draw rectangles
    display.fill_rect(20, 50, 60, 40, st7789.RED)
    display.fill_rect(90, 50, 60, 40, st7789.GREEN)
    display.fill_rect(160, 50, 60, 40, st7789.BLUE)
    
    # Draw a simple smiley
    center_x, center_y = 120, 140
    # Face
    for x in range(center_x-20, center_x+20):
        for y in range(center_y-20, center_y+20):
            if (x-center_x)**2 + (y-center_y)**2 <= 400:
                display.pixel(x, y, st7789.YELLOW)
    
    # Eyes
    display.fill_rect(110, 130, 4, 4, st7789.BLACK)
    display.fill_rect(126, 130, 4, 4, st7789.BLACK)
    
    # Smile
    for x in range(110, 130):
        y = 145 + abs(x-120)//4
        display.pixel(x, y, st7789.BLACK)
    
    time.sleep(3)

def demo_audio():
    """Demonstrate buzzer capabilities"""
    show_text("AUDIO TEST\n\nBuzzer & Melodies", st7789.MAGENTA)
    time.sleep(1)
    
    # Simple beeps
    show_text("Simple Beeps", st7789.WHITE)
    for freq in [400, 600, 800, 1000, 1200]:
        beep(freq, 0.2)
        time.sleep(0.1)
    
    # Play a simple melody (Twinkle Twinkle)
    show_text("Playing Melody:\nTwinkle Twinkle", st7789.GREEN)
    
    melody = [262, 262, 392, 392, 440, 440, 392,  # C C G G A A G
              349, 349, 330, 330, 294, 294, 262]  # F F E E D D C
    
    for note in melody:
        beep(note, 0.3)
        time.sleep(0.05)
    
    time.sleep(1)

def demo_led():
    """Demonstrate LED patterns"""
    show_text("LED TEST\n\nDifferent Patterns", st7789.YELLOW)
    time.sleep(1)
    
    # Simple blink
    show_text("Simple Blink", st7789.WHITE)
    for _ in range(6):
        led.on()
        time.sleep(0.3)
        led.off()
        time.sleep(0.3)
    
    # Fast blink
    show_text("Fast Blink", st7789.WHITE)
    for _ in range(10):
        led.on()
        time.sleep(0.1)
        led.off()
        time.sleep(0.1)
    
    # SOS pattern
    show_text("SOS Pattern", st7789.RED)
    
    def short(): led.on(); time.sleep(0.2); led.off(); time.sleep(0.2)
    def long(): led.on(); time.sleep(0.6); led.off(); time.sleep(0.2)
    
    # S.O.S
    for _ in range(3): short()  # S
    time.sleep(0.3)
    for _ in range(3): long()   # O
    time.sleep(0.3)
    for _ in range(3): short()  # S
    
    time.sleep(2)

def demo_joystick():
    """Demonstrate joystick input"""
    show_text("JOYSTICK TEST\n\nPress any direction\nor center button", st7789.CYAN)
    
    timeout = time.time() + 10  # 10 second timeout
    pressed_directions = set()
    
    while time.time() < timeout and len(pressed_directions) < 3:
        if not joy_up.value() and 'UP' not in pressed_directions:
            show_text("UP pressed!", st7789.GREEN)
            beep(800, 0.2)
            pressed_directions.add('UP')
            time.sleep(1)
        elif not joy_down.value() and 'DOWN' not in pressed_directions:
            show_text("DOWN pressed!", st7789.GREEN)
            beep(600, 0.2)
            pressed_directions.add('DOWN')
            time.sleep(1)
        elif not joy_left.value() and 'LEFT' not in pressed_directions:
            show_text("LEFT pressed!", st7789.GREEN)
            beep(400, 0.2)
            pressed_directions.add('LEFT')
            time.sleep(1)
        elif not joy_right.value() and 'RIGHT' not in pressed_directions:
            show_text("RIGHT pressed!", st7789.GREEN)
            beep(1000, 0.2)
            pressed_directions.add('RIGHT')
            time.sleep(1)
        elif not joy_select.value() and 'SELECT' not in pressed_directions:
            show_text("SELECT pressed!", st7789.GREEN)
            beep(1200, 0.2)
            pressed_directions.add('SELECT')
            time.sleep(1)
        
        time.sleep(0.1)
    
    if len(pressed_directions) >= 3:
        show_text("Great job!\nJoystick working!", st7789.GREEN)
    else:
        show_text("Joystick test\ncomplete", st7789.WHITE)
    
    time.sleep(2)

def demo_rfid():
    """Demonstrate RFID reading"""
    global cards_read
    
    if not rfid_available:
        show_text("RFID TEST\n\nRFID module not\navailable\n\nSkipping...", st7789.YELLOW)
        time.sleep(3)
        return
    
    show_text("RFID TEST\n\nPlace RFID card\nnear reader...", st7789.ORANGE)
    
    timeout = time.time() + 15  # 15 second timeout
    
    while time.time() < timeout:
        if rfid and rfid.any():
            try:
                data = rfid.read()
                if data and len(data) >= 8:
                    card_id = data.hex().upper()
                    cards_read += 1
                    
                    show_text(f"CARD DETECTED!\n\nID: {card_id[:16]}\n\nCard #{cards_read}", st7789.GREEN)
                    beep(1500, 0.3)
                    led.on()
                    time.sleep(2)
                    led.off()
                    time.sleep(1)
                    break
            except:
                pass
        
        # Show waiting animation
        dots = "." * ((int(time.time()) % 4) + 1)
        show_text(f"RFID TEST\n\nWaiting{dots}    \n\nPlace card near reader", st7789.ORANGE)
        time.sleep(0.5)
    
    if cards_read == 0:
        show_text("No RFID cards\ndetected.\n\nThat's OK!", st7789.YELLOW)
        time.sleep(2)

def demo_wifi():
    """Demonstrate WiFi capabilities"""
    show_text("WiFi TEST\n\nScanning networks...", st7789.BLUE)
    
    try:
        wlan.active(True)
        networks = wlan.scan()
        
        if networks:
            show_text(f"WiFi Working!\n\nFound {len(networks)} networks\n\nCheck console for\ndetails", st7789.GREEN)
            
            print(f"\n=== WiFi Networks Found ({len(networks)}) ===")
            for i, (ssid, bssid, channel, rssi, authmode, hidden) in enumerate(networks[:5]):
                ssid_name = ssid.decode('utf-8') if isinstance(ssid, bytes) else str(ssid)
                security = "Open" if authmode == 0 else "Secured"
                print(f"{i+1}. {ssid_name} | Signal: {rssi}dBm | {security}")
            
            beep(1000, 0.3)
        else:
            show_text("WiFi active but\nno networks found", st7789.YELLOW)
            beep(500, 0.5)
    
    except Exception as e:
        show_text("WiFi test failed\n\nCheck hardware", st7789.RED)
        print(f"WiFi error: {e}")
        beep(300, 0.5)
    
    time.sleep(3)

def demo_system_info():
    """Show system information"""
    # Get system info
    free_mem = gc.mem_free() // 1024  # KB
    used_mem = gc.mem_alloc() // 1024  # KB
    uptime = int(time.time() - start_time)
    device_id = unique_id().hex().upper()[:8]
    
    show_text(f"SYSTEM INFO\n\nMemory: {free_mem}KB free\nUptime: {uptime}s\nDevice: {device_id}\nCards read: {cards_read}", st7789.CYAN)
    
    print(f"\n=== ReadPi System Information ===")
    print(f"Free Memory: {free_mem}KB")
    print(f"Used Memory: {used_mem}KB") 
    print(f"Uptime: {uptime} seconds")
    print(f"Device ID: {device_id}")
    print(f"RFID Cards Read: {cards_read}")
    print(f"RFID Available: {rfid_available}")
    print(f"WiFi Available: {wlan.active()}")
    
    time.sleep(4)

def demo_complete():
    """Demo completion screen"""
    components = ["Display", "Audio", "LED", "Joystick", "WiFi"]
    if rfid_available:
        components.append("RFID")
    
    show_text("DEMO COMPLETE!\n\nAll systems tested:\n" + "\n".join(f"✓ {comp}" for comp in components), st7789.GREEN)
    
    # Victory melody
    victory = [523, 659, 784, 1047, 784, 1047]
    for note in victory:
        beep(note, 0.2)
        time.sleep(0.1)
    
    time.sleep(3)
    
    # Instructions for next steps
    show_text("Ready for your\nproject!\n\nCheck console for\nmore details", st7789.CYAN)
    
    print(f"\n{'='*40}")
    print("🎉 ReadPi Demo Complete!")
    print(f"{'='*40}")
    print("\nHardware components tested:")
    for comp in components:
        print(f"✓ {comp}")
    if not rfid_available:
        print("⚠ RFID - Not available (pin conflict)")
    
    print("\nWhat you can do next:")
    print("• Modify this code for your own projects")
    print("• Use the Thonny console to experiment")
    print("• Try the individual examples in the official folder")
    print("• Build your own RFID applications")
    print("\nHave fun building with ReadPi! 🚀")
    
    time.sleep(5)

# ===== MAIN DEMO LOOP =====
def run_demo():
    """Run the complete ReadPi demonstration"""
    print("\n" + "="*50)
    print("🚀 Starting ReadPi Complete Demo")
    print("="*50)
    print("\nThis demo will show you everything the ReadPi can do:")
    print("• Display graphics and text")
    print("• Play sounds and melodies") 
    print("• Control LED patterns")
    print("• Read joystick input")
    if rfid_available:
        print("• Scan RFID cards")
    else:
        print("• RFID module (not available)")
    print("• Test WiFi connectivity")
    print("• Show system information")
    print("\nWatch the screen and listen for audio feedback!")
    print("-" * 50)
    
    try:
        demo_welcome()
        demo_display()
        demo_audio()
        demo_led()
        demo_joystick()
        demo_rfid()
        demo_wifi()
        demo_system_info()
        demo_complete()
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
        show_text("Demo stopped\nby user", st7789.YELLOW)
    except Exception as e:
        print(f"Demo error: {e}")
        show_text(f"Error occurred:\n{str(e)[:20]}", st7789.RED)
        beep(300, 1)
    finally:
        # Cleanup
        led.off()
        buzzer.duty_u16(0)
        buzzer.deinit()
        wlan.active(False)

# Auto-start when file is run
if __name__ == "__main__":
    run_demo() 