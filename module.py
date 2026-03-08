import wifi
import socketpool
import adafruit_minimqtt.adafruit_minimqtt as MQTT
import board
import adafruit_bme680
import json
import time

# Connect Pico to wi-fi (mine for now while testing)
WIFI_SSID = "Reef"
WIFI_PASSWORD = "Alexandria"
MODULE_ID = "m01" # Make sure to change this for every pico
LAPTOP_IP = "192.168.2.45" # Also change this depending on where and what we test this on

wifi.radio.connect(WIFI_SSID, WIFI_PASSWORD)
print("Successfully Connected. IP:", wifi.radio.ipv4_address)

# Create a socket
pool = socketpool.SocketPool(wifi.radio)

# Create MQTT client with necessary information on standard port
mqtt_client = MQTT.MQTT(broker=LAPTOP_IP, port=1883, socket_pool=pool)

mqtt_client.connect()
print("Connected using MQTT")

# Create i2c protocol for the pico to be able to speak to the bme680
i2c = board.I2C()
bme = adafruit_bme680.Adafruit_BME680_I2C(i2c)

# Data sending loop
while True:
    # Convert python dictionary to json
    string = json.dumps({"id": MODULE_ID, "temperature": bme.temperature, "humidity": bme.relative_humidity, "pressure": bme.pressure, "gas": bme.gas,})
    
    # Send json string to laptop under station/m#/data
    mqtt_client.publish("station/" + MODULE_ID + '/data', string)
    print("Sent:", string)
    
    # Wait 1 second to send at 1Hz
    time.sleep(1)