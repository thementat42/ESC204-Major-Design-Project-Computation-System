import wifi
import socketpool
import adafruit_minimqtt.adafruit_minimqtt as MQTT
import board
import adafruit_bme680
import json
import time
import analogio
import busio
import adafruit_gps

# Connect Pico to wi-fi (mine for now while testing)
WIFI_SSID = "Reef"
WIFI_PASSWORD = "Alexandria"
MODULE_ID = "m01" # Make sure to change this for every pico
LAPTOP_IP = "192.168.2.45" # Also change this depending on where and what we test this on
ADC_HIGH = 65535

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

photoresistor_pin = board.GP26_A0
photoresistor = analogio.AnalogIn(photoresistor_pin)
ADC_REF = photoresistor.reference_voltage

def adc_to_voltage(adc_value):
    return ADC_REF * (float(adc_value)/float(ADC_HIGH))

tx_pin = board.GP0  # can be any pin marked TX (see pin map diagram)
rx_pin = board.GP1  # can be any pin marked RX (see pin map diagram)
uart = busio.UART(tx_pin, rx_pin, baudrate=9600, timeout=10)

gps = adafruit_gps.GPS(uart, debug = False)


# Turn on just minimum info (RMC only, location):
gps.send_command(b'PMTK314,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
gps.send_command(b"PMTK220,1000")  # 1Hz update rate

#* Other options for info
#? Turn on the basic GGA and RMC info (what you typically want)
# gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
#? Turn on the basic GGA and RMC info + VTG for speed in km/h
# gps.send_command(b"PMTK314,0,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
#? Turn off everything:
# gps.send_command(b'PMTK314,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
#? Turn on everything (not all of it is parsed!)
# gps.send_command(b'PMTK314,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0')

# Data sending loop
while True:
    # Convert python dictionary to json
    string = json.dumps({"id": MODULE_ID, "temperature": bme.temperature, "humidity": bme.relative_humidity, "pressure": bme.pressure, "gas": bme.gas, "light": adc_to_voltage(photoresistor.value)})
    
    # Send json string to laptop under station/m#/data
    mqtt_client.publish("station/" + MODULE_ID + '/data', string)
    print("Sent:", string)
    
    # Wait 1 second to send at 1Hz
    time.sleep(1)