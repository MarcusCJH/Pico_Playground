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

class MelodyBuzzer:
    def __init__(self, pin_number=15):
        """Initialize the buzzer with the specified pin number"""
        self.buzzer = PWM(Pin(pin_number))
        self.stop()

    def play_note(self, frequency, duration):
        """Play a single note of given frequency for specified duration"""
        if frequency == 0:  # REST
            self.stop()
        else:
            self.buzzer.duty_u16(5000)
            self.buzzer.freq(frequency)
        time.sleep(duration)
        self.stop()

    def stop(self):
        """Stop the buzzer"""
        self.buzzer.duty_u16(0)

    def play_melody(self, melody, tempo=120):
        """
        Play a melody defined as a list of (note, duration) tuples
        tempo is in beats per minute
        """
        beat_duration = 60 / tempo
        for note, beats in melody:
            frequency = NOTES.get(note, 0)
            duration = beats * beat_duration
            self.play_note(frequency, duration)

    def play_happy_birthday(self):
        """Play Happy Birthday melody"""
        happy_birthday = [
            ('C4', 0.75), ('C4', 0.25), ('D4', 1),
            ('C4', 1), ('F4', 1), ('E4', 2),
            ('C4', 0.75), ('C4', 0.25), ('D4', 1),
            ('C4', 1), ('G4', 1), ('F4', 2),
            ('C4', 0.75), ('C4', 0.25), ('C5', 1),
            ('A4', 1), ('F4', 1), ('E4', 1), ('D4', 2),
            ('B4', 0.75), ('B4', 0.25), ('A4', 1),
            ('F4', 1), ('G4', 1), ('F4', 2),
        ]
        self.play_melody(happy_birthday, tempo=100)

    def play_jingle_bells(self):
        """Play Jingle Bells melody"""
        jingle_bells = [
            ('E4', 1), ('E4', 1), ('E4', 2),
            ('E4', 1), ('E4', 1), ('E4', 2),
            ('E4', 1), ('G4', 1), ('C4', 1.5), ('D4', 0.5),
            ('E4', 4),
            ('F4', 1), ('F4', 1), ('F4', 1.5), ('F4', 0.5),
            ('F4', 1), ('E4', 1), ('E4', 1), ('E4', 0.5), ('E4', 0.5),
            ('E4', 1), ('D4', 1), ('D4', 1), ('E4', 1),
            ('D4', 2), ('G4', 2),
        ]
        self.play_melody(jingle_bells, tempo=120)

    def play_rickroll(self):
        """Play Never Gonna Give You Up main melody sequence"""
        sequence_a = [
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

        sequence_b = [
            # Bridge section
            ('C5', 0.5), ('Bb4', 0.5), ('G4', 1),
            ('F4', 0.5), ('G4', 0.5), ('F4', 1),
            ('REST', 0.5),
            ('G4', 0.5), ('Bb4', 0.5), ('C5', 1),
            ('Bb4', 0.5), ('G4', 0.5), ('F4', 1),
            ('REST', 0.5),
        ]

        # Play the full sequence
        self.play_melody(sequence_a, tempo=114)
        self.play_melody(sequence_a, tempo=114)  # Repeat main sequence
        self.play_melody(sequence_b, tempo=114)  # Bridge
        self.play_melody(sequence_a, tempo=114)  # Return to main sequence

# Example usage
if __name__ == "__main__":
    buzzer = MelodyBuzzer()
    #print("Playing Happy Birthday...")
    #buzzer.play_happy_birthday()
    #time.sleep(1)
    print("Playing Jingle Bells...")
    buzzer.play_jingle_bells()
    #time.sleep(1)
    #print("Never gonna give you up...")
    #buzzer.play_rickroll() 