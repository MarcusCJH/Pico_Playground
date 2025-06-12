"""
Pico Dual Expander Test Program
This program demonstrates usage of buzzer and LED components with the Pico Dual Expander board.

Pin Layout and Color Coding (Left Side Organization):

1. Buzzer:
   - Signal  -> GP15 [ORANGE] (PWM capable pin)
   - GND     -> GND  [BLACK]  (Use nearest GND)

2. Built-in Components:
   - LED     -> GP21 [PURPLE] (for visual feedback)
"""

from machine import Pin, PWM
import time

# Musical notes frequencies in Hz
NOTES = {
    'C4': 262,
    'D4': 294,
    'E4': 330,
    'F4': 349,
    'G4': 392,
    'A4': 440,
    'Bb4': 466,
    'B4': 494,
    'C5': 523,
    'D5': 587,
    'E5': 659,
    'F5': 698,
    'G5': 784,
    'A5': 880,
    'REST': 0
}

class PicoExpanderTest:
    def __init__(self):
        # Initialize an external LED on GP21 - Already on board
        self.external_led = Pin(21, Pin.OUT)
        
        # Initialize buzzer on GP15
        self.buzzer = PWM(Pin(15))
        self.buzzer.duty_u16(0)  # Start with buzzer off
        
        print("Pico Expander Test initialized!")
        print("\nComponent Connections:")
        print("- Buzzer: GP15")
        print("- LED: GP21 (visual feedback)")
    
    def play_note(self, note, duration):
        """Play a single note for the specified duration"""
        frequency = NOTES.get(note, 0)
        if frequency == 0:  # REST
            self.buzzer.duty_u16(0)
        else:
            self.buzzer.duty_u16(5000)  # Set volume
            self.buzzer.freq(frequency)
            self.external_led.on()  # Visual feedback
        time.sleep(duration)
        self.buzzer.duty_u16(0)
        self.external_led.off()
    
    def play_melody(self, melody, tempo=120):
        """Play a melody defined as a list of (note, duration) tuples"""
        beat_duration = 60 / tempo
        for note, beats in melody:
            self.play_note(note, beats * beat_duration)
            time.sleep(0.05)  # Small gap between notes
    
    def play_super_mario(self):
        """Play Super Mario Bros theme"""
        mario_melody = [
            ('E5', 0.5), ('E5', 0.5), ('REST', 0.5), ('E5', 0.5),
            ('REST', 0.5), ('C5', 0.5), ('E5', 0.5), ('REST', 0.5),
            ('G5', 0.5), ('REST', 1.5),
            ('G4', 0.5), ('REST', 1.5),
            
            # Repeat with variation
            ('C5', 0.5), ('REST', 1), ('G4', 0.5), ('REST', 1),
            ('E4', 0.5), ('REST', 1), ('A4', 0.5), ('REST', 0.5),
            ('B4', 0.5), ('REST', 0.5), ('Bb4', 0.5), ('A4', 0.5),
            
            ('G4', 0.75), ('E5', 0.75), ('G5', 0.75), ('A5', 0.5),
            ('F5', 0.5), ('G5', 0.5), ('REST', 0.5), ('E5', 0.5),
            ('C5', 0.5), ('D5', 0.5), ('B4', 1),
        ]
        print("Playing Super Mario Bros theme...")
        self.play_melody(mario_melody, tempo=160)
    
    def play_tetris(self):
        """Play Tetris theme"""
        tetris_melody = [
            ('E5', 1), ('B4', 0.5), ('C5', 0.5), ('D5', 1), ('C5', 0.5), ('B4', 0.5),
            ('A4', 1), ('A4', 0.5), ('C5', 0.5), ('E5', 1), ('D5', 0.5), ('C5', 0.5),
            ('B4', 1.5), ('C5', 0.5), ('D5', 1), ('E5', 1),
            ('C5', 1), ('A4', 1), ('A4', 1), ('REST', 0.5),
            
            ('D5', 1.5), ('F5', 0.5), ('A5', 1), ('G5', 0.5), ('F5', 0.5),
            ('E5', 1.5), ('C5', 0.5), ('E5', 1), ('D5', 0.5), ('C5', 0.5),
            ('B4', 1), ('B4', 0.5), ('C5', 0.5), ('D5', 1), ('E5', 1),
            ('C5', 1), ('A4', 1), ('A4', 1), ('REST', 0.5),
        ]
        print("Playing Tetris theme...")
        self.play_melody(tetris_melody, tempo=140)

    def play_rickroll(self):
        """Play Never Gonna Give You Up"""
        rickroll_melody = [
            # First phrase
            ('F4', 0.5), ('G4', 0.5), 
            ('Bb4', 0.5), ('G4', 0.5),
            ('D5', 1), ('D5', 0.5), ('C5', 1.5),
            ('REST', 0.5),
            
            # Second phrase
            ('F4', 0.5), ('G4', 0.5),
            ('Bb4', 0.5), ('G4', 0.5),
            ('C5', 1), ('C5', 0.5), ('Bb4', 1),
            ('REST', 0.5),
            
            # Third phrase
            ('F4', 0.5), ('G4', 0.5),
            ('Bb4', 0.5), ('G4', 0.5),
            ('Bb4', 0.5), ('C5', 0.5), ('G4', 0.5), ('F4', 0.5),
            ('F4', 1), ('G4', 0.5), ('Bb4', 1),
            ('REST', 0.5),
        ]
        print("Playing Never Gonna Give You Up...")
        self.play_melody(rickroll_melody, tempo=114)
    
    def run_demo(self):
        """Run the music demo"""
        print("Starting Pico Music Box Demo...")
        print("Available melodies:")
        print("1. Super Mario Bros Theme")
        print("2. Tetris Theme")
        print("3. Never Gonna Give You Up")
        
        # Play startup melody
        startup_melody = [
            ('C4', 0.2), ('E4', 0.2), ('G4', 0.2), ('C5', 0.4)
        ]
        self.play_melody(startup_melody, tempo=120)
        time.sleep(1)
        
        while True:
            print("\nPlaying all melodies in sequence...")
            
            # Play Super Mario
            self.play_super_mario()
            time.sleep(2)  # Pause between melodies
            
            # Play Tetris
            self.play_tetris()
            time.sleep(2)  # Pause between melodies
            
            # Play Rickroll
            self.play_rickroll()
            time.sleep(2)  # Pause between melodies

def main():
    tester = PicoExpanderTest()
    tester.run_demo()

if __name__ == "__main__":
    main() 