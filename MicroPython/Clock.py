import network
import time
import ntptime
from machine import Pin, I2C, SoftI2C
import ssd1306
from time import sleep

# OLED display settings - CORRECTED PINS
OLED_WIDTH = 128
OLED_HEIGHT = 64
OLED_SDA_PIN = 4   # D2 on NodeMCU (GPIO4)
OLED_SCL_PIN = 5   # D1 on NodeMCU (GPIO5)

# WiFi credentials
WIFI_SSID = "A55"
WIFI_PASSWORD = "87653214"

# Initialize I2C with correct pins
i2c = I2C(scl=Pin(OLED_SCL_PIN), sda=Pin(OLED_SDA_PIN), freq=400000)
# Alternatively try SoftI2C if hardware I2C doesn't work:
# i2c = SoftI2C(scl=Pin(OLED_SCL_PIN), sda=Pin(OLED_SDA_PIN), freq=400000)

oled = ssd1306.SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c)

def connect_wifi():
    """Connect to WiFi network"""
    oled.fill(0)
    oled.text("Connecting to", 0, 0)
    oled.text("WiFi...", 0, 10)
    oled.show()
    
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print("Connecting to WiFi...")
        sta_if.active(True)
        sta_if.connect(WIFI_SSID, WIFI_PASSWORD)
        
        # Wait for connection with timeout
        for i in range(10):
            if sta_if.isconnected():
                oled.fill(0)
                oled.text("WiFi connected!", 0, 0)
                x = "IP address:"
                y = str(sta_if.ifconfig()[0])
                oled.text(x, 0, 15)
                oled.text(y, 0, 30)
                oled.show()
                sleep(2)
                print("WiFi connected!")
                print("IP address:", sta_if.ifconfig()[0])
                
                break
            print("Waiting...", i)
            time.sleep(1)
    
    return sta_if.isconnected()

def get_ntp_time():
    """Get time from NTP server"""
    try:
        oled.fill(0)
        oled.text("Getting time", 0, 0)
        oled.text("from NTP...", 0, 10)
        oled.show()
        print("Getting time from NTP...")
        
        ntptime.settime()
        print("NTP time set successfully!")
        return True
    except Exception as e:
        print("NTP error:", e)
        return False

def format_time(seconds):
    """Format seconds to HH:MM:SS"""
    hours = (seconds // 3600) % 24
    minutes = (seconds // 60) % 60
    secs = seconds % 60
    return "{:02d}:{:02d}:{:02d}".format(hours, minutes, secs)

def display_time(seconds, source):
    """Display time on OLED"""
    oled.fill(0)
    time_str = format_time(seconds)
    
    # Display time
    oled.text(time_str, 20, 20)
    
    # Display time source
    oled.text("Source: " + source, 0, 40)
    
    # Display WiFi status
    sta_if = network.WLAN(network.STA_IF)
    if sta_if.isconnected():
        oled.text("WiFi: Connected", 0, 50)
    else:
        oled.text("WiFi: Offline", 0, 50)
    
    oled.show()

def test_oled():
    """Test OLED connection"""
    try:
        oled.fill(0)
        oled.text("OLED Test", 0, 0)
        oled.text("Success!", 0, 20)
        oled.show()
        print("OLED test passed!")
        return True
    except Exception as e:
        print("OLED test failed:", e)
        return False

def main():
    print("Starting program...")
    
    # Test OLED first
    if not test_oled():
        print("OLED not detected! Check connections.")
        return
    
    # Try to connect to WiFi and get NTP time
    wifi_connected = connect_wifi()
    ntp_success = False
    
    if wifi_connected:
        ntp_success = get_ntp_time()
    
    # Initialize time
    if ntp_success:
        # Get current time from RTC (set by NTP)
        current_time = time.time()
        time_source = "NTP"
        print("Using NTP time")
    else:
        # Start from zero
        current_time = 0
        time_source = "Local"
        print("Using local time")
    
    last_update = time.ticks_ms()
    
    print("Starting clock...")
    
    # Main loop
    while True:
        current_ticks = time.ticks_ms()
        
        # Update time every second
        if time.ticks_diff(current_ticks, last_update) >= 1000:
            if ntp_success:
                current_time = time.time()
            else:
                current_time += 1
                
            last_update = current_ticks
            
            # Display time
            display_time(int(current_time), time_source)
        
        time.sleep(0.1)

# Run the main function
if __name__ == "__main__":
    main()
