import network
import socket
import machine
import gc

# AP settings
AP_SSID = "ESP8266-AP"
AP_PASSWORD = "12345678"
AP_IP = "192.168.4.1"

class WebServer:
    def __init__(self):
        self.led = machine.Pin(2, machine.Pin.OUT)
        self.led.on()
        
        # Setup AP
        ap = network.WLAN(network.AP_IF)
        ap.active(True)
        ap.config(essid=AP_SSID, password=AP_PASSWORD)
        ap.ifconfig((AP_IP, '255.255.255.0', AP_IP, AP_IP))
        
        print("AP Ready:", AP_SSID)
        print("Connect to:", AP_IP)

    def create_response(self, content, content_type="text/html"):
        return """HTTP/1.1 200 OK
Content-Type: """ + content_type + """
Connection: close

""" + content

    def handle_request(self, client):
        request = client.recv(1024).decode()
        
        if 'GET / ' in request:
            html = """<html><body>
            <h1>ESP8266 Control</h1>
            <p>Free memory: """ + str(gc.mem_free()) + """ bytes</p>
            <button onclick="fetch('/ledon')">LED ON</button>
            <button onclick="fetch('/ledoff')">LED OFF</button>
            <script>function fetch(url){var xhr=new XMLHttpRequest();xhr.open('GET',url);xhr.send();}</script>
            </body></html>"""
            client.send(self.create_response(html))
        
        elif 'GET /ledon' in request:
            self.led.off()
            client.send(self.create_response("LED ON", "text/plain"))
        
        elif 'GET /ledoff' in request:
            self.led.on()
            client.send(self.create_response("LED OFF", "text/plain"))
        
        else:
            client.send(self.create_response("Page not found", "text/plain"))
        
        client.close()
        gc.collect()

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', 80))
        sock.listen(1)
        
        print("Server started")
        while True:
            client, addr = sock.accept()
            print("Client:", addr[0])
            self.handle_request(client)

# Start server
server = WebServer()
server.run()