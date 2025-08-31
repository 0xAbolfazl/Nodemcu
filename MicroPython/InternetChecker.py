import network
import time
import urequests
from machine import Pin, I2C, SoftI2C
import ssd1306
import gc

# OLED display settings
OLED_WIDTH = 128
OLED_HEIGHT = 64
OLED_SDA_PIN = 4   # D2 on NodeMCU (GPIO4)
OLED_SCL_PIN = 5   # D1 on NodeMCU (GPIO5)

# WiFi credentials
WIFI_SSID = "A55"
WIFI_PASSWORD = "87653214"

# Speed test server
SPEED_TEST_URL = "http://httpbin.org/bytes/1024"  # 1KB test file
PING_URL = "http://httpbin.org/get"

# Timing constants - Reduced timeouts for faster detection
TEST_INTERVAL = 3000        # Test every 3 seconds (reduced from 5)
OFFLINE_DELAY = 1000        # 1 second delay before showing offline (reduced from 2)
DISCONNECT_BLINK_INTERVAL = 200  # 400ms blink interval
OFFLINE_BLINK_INTERVAL = 200    # 400ms blink interval for offline state
TEST_TIMEOUT = 2000         # 2 seconds timeout for each test

# Initialize I2C and OLED
i2c = I2C(scl=Pin(OLED_SCL_PIN), sda=Pin(OLED_SDA_PIN))
oled = ssd1306.SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c)

def connect_wifi():
    """Connect to WiFi network"""
    oled.fill(0)
    oled.text("Connecting to", 0, 0)
    oled.text("WiFi...", 0, 10)
    oled.show()
    
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        sta_if.active(True)
        sta_if.connect(WIFI_SSID, WIFI_PASSWORD)
        
        for i in range(15):  # Reduced from 20 to 15 seconds timeout
            if sta_if.isconnected():
                break
            time.sleep(1)
    
    return sta_if.isconnected()

def ping_test():
    """Measure ping time with timeout"""
    try:
        start_time = time.ticks_ms()
        response = urequests.get(PING_URL, timeout=TEST_TIMEOUT/1000)
        end_time = time.ticks_ms()
        response.close()
        ping_time = time.ticks_diff(end_time, start_time)
        return ping_time
    except:
        return None

def download_speed_test():
    """Measure download speed with timeout"""
    try:
        start_time = time.ticks_ms()
        response = urequests.get(SPEED_TEST_URL, timeout=TEST_TIMEOUT/1000)
        data = response.content
        end_time = time.ticks_ms()
        response.close()
        
        download_time = time.ticks_diff(end_time, start_time) / 1000  # seconds
        data_size = len(data)  # bytes
        speed_kbps = (data_size * 8) / download_time / 1024  # kbps
        
        return speed_kbps
    except:
        return None

def upload_speed_test():
    """Measure upload speed with timeout"""
    try:
        # Simulate upload by posting small data
        test_data = "x" * 512  # 512 bytes test data
        start_time = time.ticks_ms()
        response = urequests.post("http://httpbin.org/post", data=test_data, timeout=TEST_TIMEOUT/1000)
        end_time = time.ticks_ms()
        response.close()
        
        upload_time = time.ticks_diff(end_time, start_time) / 1000  # seconds
        data_size = len(test_data)  # bytes
        speed_kbps = (data_size * 8) / upload_time / 1024  # kbps
        
        return speed_kbps
    except:
        return None

def display_offline():
    """Display offline message with white background and black text"""
    oled.fill(1)  # Fill with white (1 = white)
    oled.text("OFFLINE", 40, 28, 0)  # Black text (0 = black)
    oled.show()

def display_disconnected():
    """Display disconnected message with white background and black text"""
    oled.fill(1)  # Fill with white (1 = white)
    oled.text("DISCONNECTED", 20, 28, 0)  # Black text (0 = black)
    oled.show()

def display_results(ping, download, upload, status):
    """Display results on OLED"""
    oled.fill(0)
    
    # Display status
    oled.text("WiFi: " + status, 0, 0)
    
    if status == "Connected":
        # Display ping
        if ping is not None:
            oled.text("Ping: {}ms".format(int(ping)), 0, 15)
        else:
            oled.text("Ping: Failed", 0, 15)
        
        # Display download speed
        if download is not None:
            oled.text("DN: {:.1f}kbps".format(download), 0, 30)
        else:
            oled.text("DN: Failed", 0, 30)
        
        # Display upload speed
        if upload is not None:
            oled.text("UP: {:.1f}kbps".format(upload), 0, 45)
        else:
            oled.text("UP: Failed", 0, 45)
    
    oled.show()

def display_loading(message):
    """Display loading message"""
    oled.fill(0)
    oled.text(message, 0, 20)
    oled.show()

def all_tests_failed(ping, download, upload):
    """Check if all speed tests failed"""
    return ping is None and download is None and upload is None

def any_test_succeeded(ping, download, upload):
    """Check if any speed test succeeded"""
    return ping is not None or download is not None or upload is not None

def main():
    print("Internet Speed Test Started")
    
    # Initial connection
    wifi_connected = connect_wifi()
    
    last_test_time = time.ticks_ms()
    offline_timer = 0
    disconnect_timer = 0
    last_blink_time = 0
    offline_blink_state = False
    disconnect_blink_state = False
    
    # State tracking
    was_connected = wifi_connected
    connection_lost_time = 0
    last_offline_test_time = 0
    
    # Test results cache
    last_ping = None
    last_download = None
    last_upload = None
    all_failed_state = False

    while True:
        current_time = time.ticks_ms()
        
        # Check WiFi status
        sta_if = network.WLAN(network.STA_IF)
        is_connected = sta_if.isconnected()
        current_status = "Connected" if is_connected else "Disconnected"
        
        # Handle connection state changes
        if not is_connected and was_connected:
            # Just got disconnected from AP
            connection_lost_time = current_time
            disconnect_timer = current_time
            all_failed_state = False
            print("Disconnected from access point")
        
        # Update previous connection state
        was_connected = is_connected
        
        # State 1: Connected to AP
        if is_connected:
            # Perform speed test regularly, even in offline state
            test_interval = TEST_INTERVAL
            if all_failed_state:
                test_interval = 2000  # Test every 2 seconds in offline state
            
            if time.ticks_diff(current_time, last_test_time) >= test_interval:
                ping = ping_test()
                download = download_speed_test()
                upload = upload_speed_test()
                
                # Check if test results changed
                results_changed = (ping != last_ping or download != last_download or upload != last_upload)
                
                # Update cache
                last_ping = ping
                last_download = download
                last_upload = upload
                
                # Check if all tests failed
                if all_tests_failed(ping, download, upload):
                    if not all_failed_state or results_changed:
                        all_failed_state = True
                        offline_timer = current_time
                        print("All tests failed - entering offline state")
                    
                    # Blink effect for offline state
                    if time.ticks_diff(current_time, last_blink_time) >= OFFLINE_BLINK_INTERVAL:
                        offline_blink_state = not offline_blink_state
                        last_blink_time = current_time
                        
                        if offline_blink_state:
                            display_offline()
                        else:
                            oled.fill(1)  # White screen
                            oled.show()
                
                else:
                    # Some tests succeeded - exit offline state
                    if all_failed_state or results_changed:
                        all_failed_state = False
                        offline_timer = 0
                        display_results(ping, download, upload, current_status)
                        print("Tests succeeded - exiting offline state")
                
                # Print results to console
                print("Status:", current_status)
                if ping is not None: print("Ping: {}ms".format(int(ping)))
                if download is not None: print("Download: {:.1f}kbps".format(download))
                if upload is not None: print("Upload: {:.1f}kbps".format(upload))
                print("---")
                
                last_test_time = current_time
                gc.collect()  # Free memory
        
        # State 2: Disconnected from AP (DISCONNECTED with blinking)
        elif not is_connected:
            # Check if 5 seconds haven't passed since disconnection
            if time.ticks_diff(current_time, last_blink_time) >= OFFLINE_BLINK_INTERVAL:
                offline_blink_state = not offline_blink_state
                last_blink_time = current_time
                
                if offline_blink_state:
                    display_offline()
                else:
                    oled.fill(1)  # White screen
                    oled.show()

            # Blink effect for disconnected state  
            if time.ticks_diff(current_time, connection_lost_time) <= 500:
                # Blink effect every 200ms (FASTER)
                if time.ticks_diff(current_time, last_blink_time) >= DISCONNECT_BLINK_INTERVAL:
                    disconnect_blink_state = not disconnect_blink_state
                    last_blink_time = current_time
                    
                    if disconnect_blink_state:
                        display_disconnected()
                    else:
                        oled.fill(1)  # White screen
                        oled.show()
            else:
                # After 5 seconds, stay on white screen with DISCONNECTED
                display_disconnected()
        
        # Try to reconnect if disconnected
        if not is_connected:
            # Only try to reconnect if actually disconnected
            connect_wifi()
        
        time.sleep(0.1)

# Run the program
if __name__ == "__main__":
    main()
