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
# Speed test server (you can change this)
SPEED_TEST_URL = "http://httpbin.org/bytes/1024"  # 1KB test file
PING_URL = "http://httpbin.org/get"

# Initialize I2C and OLED
i2c = I2C(scl=Pin(OLED_SCL_PIN), sda=Pin(OLED_SDA_PIN))
# i2c = SoftI2C(scl=Pin(OLED_SCL_PIN), sda=Pin(OLED_SDA_PIN))  # Alternative
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
        
        for i in range(20):
            if sta_if.isconnected():
                break
            time.sleep(1)
    
    return sta_if.isconnected()

def ping_test():
    """Measure ping time"""
    try:
        start_time = time.ticks_ms()
        response = urequests.get(PING_URL)
        end_time = time.ticks_ms()
        response.close()
        ping_time = time.ticks_diff(end_time, start_time)
        return ping_time
    except:
        return None

def download_speed_test():
    """Measure download speed"""
    try:
        start_time = time.ticks_ms()
        response = urequests.get(SPEED_TEST_URL)
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
    """Measure upload speed (simulated)"""
    try:
        # Simulate upload by posting small data
        test_data = "x" * 512  # 512 bytes test data
        start_time = time.ticks_ms()
        response = urequests.post("http://httpbin.org/post", data=test_data)
        end_time = time.ticks_ms()
        response.close()
        
        upload_time = time.ticks_diff(end_time, start_time) / 1000  # seconds
        data_size = len(test_data)  # bytes
        speed_kbps = (data_size * 8) / upload_time / 1024  # kbps
        
        return speed_kbps
    except:
        return None

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
    else:
        oled.text("No Connection", 0, 20)
        oled.text("Check WiFi", 0, 35)
    
    oled.show()

def display_loading(message):
    """Display loading message"""
    oled.fill(0)
    oled.text(message, 0, 20)
    oled.show()

def main():
    print("Internet Speed Test Started")
    
    # Initial connection
    wifi_connected = connect_wifi()
    
    last_test_time = time.ticks_ms()
    test_interval = 5000  # Test every 5 seconds
    
    while True:
        current_time = time.ticks_ms()
        
        # Check WiFi status
        sta_if = network.WLAN(network.STA_IF)
        current_status = "Connected" if sta_if.isconnected() else "Disconnected"
        
        # Perform speed test every interval
        if time.ticks_diff(current_time, last_test_time) >= test_interval:
            ping = None
            download = None
            upload = None
            
            if current_status == "Connected":
               
                ping = ping_test()
                
                
                download = download_speed_test()
                
            
                upload = upload_speed_test()
            
            # Display results
            display_results(ping, download, upload, current_status)
            
            # Print results to console
            print("Status:", current_status)
            if ping: print("Ping: {}ms".format(int(ping)))
            if download: print("Download: {:.1f}kbps".format(download))
            if upload: print("Upload: {:.1f}kbps".format(upload))
            print("---")
            
            last_test_time = current_time
            gc.collect()  # Free memory
        
        
        # Try to reconnect if disconnected
        if not sta_if.isconnected():
            display_loading("Reconnecting...")
            connect_wifi()

# Run the program
if __name__ == "__main__":
    main()
