#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <ESP8266WiFi.h>
#include <WiFiUdp.h>
#include <NTPClient.h>
#include <TimeLib.h>

// OLED display dimensions
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 32

// Initialize OLED display
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// WiFi credentials
const char* ssid = "YOUR_SSID";        // Replace with your WiFi SSID
const char* password = "YOUR_PASSWORD";  // Replace with your WiFi password

// Define NTP Client to get time
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, "pool.ntp.org", 19800, 60000);  // UTC+5:30 (19800 seconds)

// Weekday names
const char* daysOfWeek[] = {"Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"};

// Month names
const char* months[] = {"Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"};

void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  
  // Initialize OLED display
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) { 
    Serial.println(F("SSD1306 allocation failed"));
    for(;;); // Don't proceed, loop forever
  }
  
  // Clear the display buffer
  display.clearDisplay();
  
  // Display startup message
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(0, 0);
  display.println("Connecting to WiFi");
  display.display();
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    display.print(".");
    display.display();
  }
  
  // Display connection success
  display.clearDisplay();
  display.setCursor(0, 0);
  display.println("WiFi connected!");
  display.print("IP: ");
  display.println(WiFi.localIP());
  display.display();
  delay(2000);
  
  // Initialize NTP client
  timeClient.begin();
  
  // Set timezone offset (UTC+5:30 for India)
  timeClient.setTimeOffset(19800);
}