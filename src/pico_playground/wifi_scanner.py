import network
import time
import urequests

class WiFiManager:
    def __init__(self):
        self.wlan = network.WLAN(network.STA_IF)
        if not self.wlan.active():
            self.wlan.active(True)
            time.sleep(1)  # Give the interface time to initialize
    
    def scan(self, sort_by_strength=True):
        """Scan for available WiFi networks"""
        print("📡 Scanning for WiFi networks...")
        networks = []
        
        try:
            scan_results = self.wlan.scan()
            for ssid, bssid, channel, rssi, authmode, hidden in scan_results:
                try:
                    ssid = ssid.decode('utf-8')
                except:
                    ssid = str(ssid)
                
                # Convert authmode to readable format
                auth_modes = {
                    0: "Open",
                    1: "WEP",
                    2: "WPA-PSK",
                    3: "WPA2-PSK",
                    4: "WPA/WPA2-PSK",
                    5: "WPA2-Enterprise",
                    6: "WPA3-PSK",
                    7: "WPA2/WPA3-PSK"
                }
                auth_str = auth_modes.get(authmode, f"Unknown ({authmode})")
                
                networks.append({
                    'ssid': ssid,
                    'channel': channel,
                    'rssi': rssi,
                    'auth_mode': auth_str,
                    'hidden': hidden,
                    'authmode': authmode
                })
            
            if sort_by_strength:
                networks.sort(key=lambda x: x['rssi'], reverse=True)
                
            return networks
            
        except Exception as e:
            print(f"❌ Scan failed: {e}")
            return []
    
    def print_networks(self, networks):
        """Pretty print the network scan results"""
        if not networks:
            print("No networks found!")
            return
            
        print("\n📶 Available Networks:")
        print("=" * 60)
        print(f"{'SSID':<32} {'Signal':<8} {'Channel':<8} {'Security':<15}")
        print("-" * 60)
        
        for net in networks:
            # Convert RSSI to signal bars
            rssi = net['rssi']
            if rssi >= -50:
                signal = "▂▄▆█"
            elif rssi >= -60:
                signal = "▂▄▆ "
            elif rssi >= -70:
                signal = "▂▄  "
            else:
                signal = "▂   "
            
            print(f"{net['ssid']:<32} {signal:<8} {net['channel']:<8} {net['auth_mode']:<15}")

    def check_captive_portal(self):
        """Check if we're behind a captive portal by trying to access a known site"""
        print("\nChecking for captive portal...")
        try:
            # Try to access a known reliable site
            response = urequests.get("http://www.google.com/generate_204", timeout=5)
            if response.status_code == 204:
                print("✅ Direct internet access available")
                return False
            else:
                print("⚠️ Captive portal detected!")
                print("This network requires web browser authentication.")
                print("Please complete these steps:")
                print("1. Connect to this network from a device with a web browser")
                print("2. Try to access any website - you should be redirected to the login page")
                print("3. Complete the authentication process")
                print("4. Once authenticated, try connecting with this device again")
                return True
        except:
            print("⚠️ Cannot verify internet access")
            return True

    def disconnect(self):
        """Safely disconnect from current network"""
        if self.wlan.isconnected():
            print("Disconnecting from current network...")
            try:
                self.wlan.disconnect()
                time.sleep(2)  # Wait for disconnect to complete
                return True
            except:
                return False
        return True

    def connect(self, ssid, password=None, timeout=20, retries=2):
        """
        Connect to a specific WiFi network
        
        Args:
            ssid: Network name to connect to
            password: Network password (optional)
            timeout: How long to wait for connection in seconds
            retries: Number of connection attempts
            
        Returns:
            bool: True if connected successfully
        """
        for attempt in range(retries):
            if attempt > 0:
                print(f"\nRetry attempt {attempt + 1}...")
                time.sleep(3)  # Wait between retries
            
            print(f"\n🔌 Connecting to {ssid}...")
            if password:
                print("Using provided password")
            
            # Ensure clean state
            if not self.disconnect():
                continue
                
            try:
                # Make sure interface is active
                if not self.wlan.active():
                    self.wlan.active(True)
                    time.sleep(1)
                
                # Try to connect
                if password:
                    self.wlan.connect(ssid, password)
                else:
                    self.wlan.connect(ssid)
                
                # Wait for connection with timeout
                current_timeout = timeout
                while current_timeout > 0 and not self.wlan.isconnected():
                    print(".", end="")
                    time.sleep(1)
                    current_timeout -= 1
                print()  # New line after dots
                
                if self.wlan.isconnected():
                    config = self.wlan.ifconfig()
                    print(f"✅ Connected to network!")
                    print(f"   IP Address: {config[0]}")
                    print(f"   Subnet Mask: {config[1]}")
                    print(f"   Gateway: {config[2]}")
                    print(f"   DNS: {config[3]}")
                    
                    # Check for captive portal
                    self.check_captive_portal()
                    return True
                else:
                    print("❌ Connection failed - timeout")
                    
            except Exception as e:
                print(f"❌ Connection failed: {e}")
                if "EPERM" in str(e):
                    print("This error might mean:")
                    print("1. The network interface is busy")
                    print("2. The system needs a moment to reset")
        
        print("\nFailed to connect after all attempts")
        return False

def main():
    wifi = WiFiManager()
    
    # First scan for networks
    networks = wifi.scan()
    wifi.print_networks(networks)
    
    # Try to connect to iPhone hotspot
    print("\n⚠️ Note: Attempting to connect to Marcus's iPhone")
    print("Using provided password for authentication")
    
    # Add a small delay before connecting
    time.sleep(2)
    wifi.connect("Marcus's iPhone", password="hehehahahoho", retries=2)

if __name__ == "__main__":
    main() 