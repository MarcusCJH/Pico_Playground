import machine
import time
from machine import Pin, ADC

# Initialize ADC for battery voltage measurement
# Using ADC0 (GP26) for battery voltage measurement
battery_adc = ADC(26)

# Constants for voltage calculation
ADC_REF_VOLTAGE = 3.3  # Reference voltage for ADC
ADC_RESOLUTION = 65535  # 16-bit ADC resolution
VOLTAGE_DIVIDER_RATIO = 3.3  # Adjusted for actual voltage divider on board

# Battery detection thresholds
BATTERY_PRESENT_THRESHOLD = 1.0  # Lowered threshold to detect battery
BATTERY_DEAD_THRESHOLD = 2.5     # Voltage threshold below which battery is considered dead
BATTERY_GOOD_THRESHOLD = 3.3     # Minimum voltage for a good battery
USB_VOLTAGE_THRESHOLD = 3.8      # Lowered threshold to detect USB power

# Battery specifications
MIN_BATTERY_VOLTAGE = 3.0  # Minimum safe voltage for LiPo
MAX_BATTERY_VOLTAGE = 4.2  # Maximum safe voltage for LiPo

def read_battery_voltage():
    """
    Read the battery voltage using ADC
    Returns voltage in volts
    """
    try:
        # Take multiple readings and average them
        readings = []
        for _ in range(5):
            adc_value = battery_adc.read_u16()
            readings.append(adc_value)
            time.sleep(0.1)  # Small delay between readings
        
        # Calculate average ADC value
        avg_adc = sum(readings) / len(readings)
        
        # Convert ADC value to voltage
        voltage = (avg_adc * ADC_REF_VOLTAGE) / ADC_RESOLUTION
        
        # Apply voltage divider ratio
        actual_voltage = voltage * VOLTAGE_DIVIDER_RATIO
        
        return actual_voltage, avg_adc  # Return both voltage and raw ADC value
    except Exception as e:
        print(f"Error reading voltage: {e}")
        return 0.0, 0

def check_battery_safety(voltage):
    """
    Check if battery voltage is within safe limits
    Returns tuple of (is_safe, message)
    """
    if voltage < MIN_BATTERY_VOLTAGE:
        return False, f"Battery voltage too low ({voltage:.2f}V < {MIN_BATTERY_VOLTAGE}V)"
    elif voltage > MAX_BATTERY_VOLTAGE:
        return False, f"Battery voltage too high ({voltage:.2f}V > {MAX_BATTERY_VOLTAGE}V)"
    return True, "Battery voltage within safe limits"

def is_usb_powered(voltage):
    """
    Check if device is powered by USB based on voltage
    Returns True if USB power is detected, False otherwise
    """
    # USB power typically provides stable voltage around 5V
    # After voltage divider, it should be around 3.3V
    return voltage >= USB_VOLTAGE_THRESHOLD

def get_battery_state(voltage):
    """
    Get detailed battery state
    Returns a tuple of (state, message, needs_action)
    """
    # Check if USB powered
    usb_powered = is_usb_powered(voltage)
    
    # If USB powered, don't check battery safety
    if usb_powered:
        return "USB_POWER", "Powered by USB", False
    
    # Check battery safety first
    is_safe, safety_message = check_battery_safety(voltage)
    if not is_safe:
        return "UNSAFE", safety_message, True
    
    # Check voltage-based states
    if voltage < BATTERY_PRESENT_THRESHOLD:
        return "NO_BATTERY", "No Battery Detected (Voltage too low)", False
    elif voltage < BATTERY_DEAD_THRESHOLD:
        return "DEAD", "Battery Dead - Replace Battery", True
    elif voltage < BATTERY_GOOD_THRESHOLD:
        return "LOW", "Battery Voltage Too Low - Charge Immediately", True
    elif voltage >= 4.0:
        return "FULL", "Fully Charged", False
    elif voltage >= 3.7:
        return "GOOD", "Battery Good", False
    else:
        return "LOW", "Battery Low - Consider Charging", True

def estimate_battery_capacity(voltage):
    """
    Estimate battery capacity based on voltage
    Returns percentage (0-100)
    """
    # LiPo battery voltage ranges
    MAX_VOLTAGE = 4.2  # Fully charged
    MIN_VOLTAGE = 3.3  # Discharged
    
    # Calculate percentage
    percentage = ((voltage - MIN_VOLTAGE) / (MAX_VOLTAGE - MIN_VOLTAGE)) * 100
    percentage = max(0, min(100, percentage))  # Clamp between 0 and 100
    
    return percentage

def main():
    print("Battery Status Monitor")
    print("---------------------")
    print("Debug Information:")
    print(f"ADC Reference Voltage: {ADC_REF_VOLTAGE}V")
    print(f"Voltage Divider Ratio: {VOLTAGE_DIVIDER_RATIO}")
    print(f"Battery Present Threshold: {BATTERY_PRESENT_THRESHOLD}V")
    print(f"USB Detection Threshold: {USB_VOLTAGE_THRESHOLD}V")
    print(f"Safe Voltage Range: {MIN_BATTERY_VOLTAGE}V - {MAX_BATTERY_VOLTAGE}V")
    print("---------------------")
    
    while True:
        try:
            # Read battery voltage
            voltage, raw_adc = read_battery_voltage()
            
            # Get battery state
            state, message, needs_action = get_battery_state(voltage)
            
            # Print detailed status
            print(f"Power Source: {'USB' if is_usb_powered(voltage) else 'Battery'}")
            print(f"Battery State: {state}")
            print(f"Raw ADC Value: {raw_adc}")
            print(f"Battery Voltage: {voltage:.2f}V")
            
            if state not in ["NO_BATTERY", "DEAD", "UNSAFE", "USB_POWER"]:
                capacity = estimate_battery_capacity(voltage)
                print(f"Estimated Capacity: {capacity:.1f}%")
            
            print(f"Status: {message}")
            
            if needs_action and not is_usb_powered(voltage):
                print("Action Required: Connect USB charger")
            elif is_usb_powered(voltage) and state == "LOW":
                print("Status: Charging in progress...")
            
            if state == "UNSAFE":
                print("WARNING: Battery voltage outside safe limits!")
                print("Please check battery connection and specifications.")
            
            print("---------------------")
            
            # Wait for 5 seconds before next reading
            time.sleep(5)
            
        except Exception as e:
            print(f"Error reading battery: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main() 