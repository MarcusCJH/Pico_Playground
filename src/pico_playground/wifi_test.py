# Network Connectivity Test for ReadPI
import network
import urequests
import socket
import time

def test_network_connectivity():
    print("🌐 Network Connectivity Test")
    print("=" * 50)
    
    # Check WiFi status
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        print("❌ WiFi not connected!")
        return False
        
    config = wlan.ifconfig()
    print(f"✅ WiFi Connected:")
    print(f"   IP: {config[0]}")
    print(f"   Gateway: {config[2]}")
    print(f"   DNS: {config[3]}")
    
    # Test 1: Basic socket connection to Google DNS
    print(f"\n🔍 Test 1: Socket connection to Google DNS (8.8.8.8)")
    try:
        sock = socket.socket()
        sock.settimeout(5)
        result = sock.connect(('8.8.8.8', 53))
        sock.close()
        print(f"✅ Socket connection successful")
    except Exception as e:
        print(f"❌ Socket connection failed: {e}")
    
    # Test 2: Try simple HTTP requests to different servers
    test_urls = [
        "http://httpbin.org/ip",
        "http://www.google.com",
        "http://example.com",
        "http://jsonplaceholder.typicode.com/posts/1",
        "http://httpbin.org/get"
    ]
    
    print(f"\n🔍 Test 2: HTTP GET requests")
    working_urls = []
    
    for url in test_urls:
        print(f"   Testing: {url}")
        try:
            response = urequests.get(url, timeout=8)
            status = response.status_code
            response.close()
            
            if status == 200:
                print(f"   ✅ SUCCESS - Status: {status}")
                working_urls.append(url)
            else:
                print(f"   ⚠️ Response: {status}")
                
        except OSError as e:
            if e.errno == 115:
                print(f"   ❌ Timeout (EINPROGRESS)")
            else:
                print(f"   ❌ Network error: {e}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        time.sleep(1)  # Brief pause between requests
    
    # Test 3: Try simple POST requests
    print(f"\n🔍 Test 3: HTTP POST requests")
    post_urls = [
        "http://httpbin.org/post",
        "http://httpbin.org/anything", 
        "http://jsonplaceholder.typicode.com/posts"
    ]
    
    test_payload = {"test": "data", "timestamp": time.time()}
    
    for url in post_urls:
        print(f"   Testing POST: {url}")
        try:
            response = urequests.post(
                url, 
                json=test_payload,
                timeout=8
            )
            status = response.status_code
            response.close()
            
            if status in [200, 201]:
                print(f"   ✅ POST SUCCESS - Status: {status}")
                working_urls.append(f"{url} (POST)")
            else:
                print(f"   ⚠️ POST Response: {status}")
                
        except OSError as e:
            if e.errno == 115:
                print(f"   ❌ POST Timeout (EINPROGRESS)")
            else:
                print(f"   ❌ POST Network error: {e}")
        except Exception as e:
            print(f"   ❌ POST Error: {e}")
        
        time.sleep(1)
    
    # Test 4: Check if it's a DNS issue
    print(f"\n🔍 Test 4: DNS Resolution Test")
    test_hosts = ["google.com", "httpbin.org", "example.com"]
    
    for host in test_hosts:
        try:
            ip = socket.getaddrinfo(host, 80)[0][-1][0]
            print(f"   ✅ {host} -> {ip}")
        except Exception as e:
            print(f"   ❌ {host} -> DNS failed: {e}")
    
    # Summary
    print(f"\n📋 SUMMARY")
    print("=" * 50)
    if working_urls:
        print(f"✅ Working URLs found:")
        for url in working_urls:
            print(f"   - {url}")
        print(f"\n💡 Recommendation: Use one of the working URLs above")
    else:
        print(f"❌ No working HTTP endpoints found")
        print(f"💡 Possible issues:")
        print(f"   - Firewall blocking HTTP requests")
        print(f"   - Router blocking external requests")
        print(f"   - DNS resolution issues")
        print(f"   - ISP restrictions")
        
    return len(working_urls) > 0

def test_local_server():
    """Test if we can reach local network servers"""
    print(f"\n🏠 Local Network Test")
    print("=" * 30)
    
    # Try to reach router/gateway
    wlan = network.WLAN(network.STA_IF)
    gateway = wlan.ifconfig()[2]
    
    print(f"Testing gateway: {gateway}")
    try:
        # Try HTTP on common router ports
        test_ports = [80, 8080, 8000]
        for port in test_ports:
            try:
                sock = socket.socket()
                sock.settimeout(2)
                result = sock.connect((gateway, port))
                sock.close()
                print(f"✅ Gateway port {port} is open")
                
                # Try HTTP request to gateway
                try:
                    response = urequests.get(f"http://{gateway}:{port}", timeout=3)
                    print(f"✅ HTTP request to gateway:{port} - Status: {response.status_code}")
                    response.close()
                except:
                    print(f"⚠️ Gateway:{port} - socket open but HTTP failed")
                break
                    
            except:
                pass
        else:
            print(f"❌ No open HTTP ports found on gateway")
            
    except Exception as e:
        print(f"❌ Gateway test failed: {e}")

if __name__ == "__main__":
    # Connect WiFi first
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.active(True)
        wlan.connect("bskm", "91469702bskm")
        
        timeout = 10
        while timeout > 0 and not wlan.isconnected():
            time.sleep(1)
            timeout -= 1
    
    if wlan.isconnected():
        test_network_connectivity()
        test_local_server()
    else:
        print("❌ Failed to connect to WiFi") 