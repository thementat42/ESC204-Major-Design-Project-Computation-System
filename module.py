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
from data_keys import *
from _mqtt import *
import ssl
import adafruit_ntp
import rtc
import adafruit_logging as logging

MODULE_ID = 1 # Make sure to change this for every pico

ADC_HIGH = 65535
BME_GAS_MIN = 10167
BME_GAS_THRESHOLD = 63930.51612903226  # High resistance = fresh air
PHOTORESISTOR_MIN = 0.01919811157142857  # volts (low voltage = bright)
PHOTORESISTOR_MAX = 3.115979861111111  # volts

# Connect Pico to wi-fi
wifi.radio.connect(WIFI_SSID, WIFI_PASSWORD)
print(f"Successfully Connected to {WIFI_SSID}")

# Create a socket
pool = socketpool.SocketPool(wifi.radio)

print("Testing DNS resolution...")
try:
    # Test 1: Can we resolve a basic website?
    google_ip = pool.getaddrinfo("google.com", 80)[0][4][0]
    print(f"Basic DNS works (Google IP: {google_ip})")
    
    # Test 2: Can we resolve HiveMQ broker?
    hivemq_ip = pool.getaddrinfo(HIVEMQ_HOST, 8883)[0][4][0]
    print(f"HiveMQ DNS works (HiveMQ IP: {hivemq_ip})")
except Exception as e:
    print(f"DNS FAILED! Error: {e}")

ssl_context = ssl.create_default_context()

ntp = adafruit_ntp.NTP(pool, tz_offset=0)
rtc.RTC().datetime = ntp.datetime
print("RTC time:", rtc.RTC().datetime)

mqtt_logger = logging.getLogger("mqtt")
mqtt_logger.setLevel(logging.DEBUG)

# Create MQTT client with necessary information on standard port
mqtt_client = MQTT.MQTT(
    broker=HIVEMQ_HOST,
    port=8883,
    username = HIVEMQ_USERNAME,
    password = HIVEMQ_PASSWORD,
    socket_pool = pool,
    ssl_context=ssl_context,
    client_id = str(MODULE_ID),
    is_ssl=True,
    keep_alive = 60
)
mqtt_client.logger = mqtt_logger

print("Connecting to HiveMQ Cloud...")
mqtt_client.connect()
print("Connected using MQTT")

# Create i2c protocol for the pico to be able to speak to the bme680
sda_pin = board.GP12  # can be any pin marked SDA
scl_pin = board.GP13  # can be any pin marked SCL

i2c = busio.I2C(scl_pin, sda_pin)
bme = adafruit_bme680.Adafruit_BME680_I2C(i2c, address = 0x76)

# Allow pico to communicate with photoresistor
photoresistor_pin = board.GP26_A0
photoresistor = analogio.AnalogIn(photoresistor_pin)
ADC_REF = photoresistor.reference_voltage

def get_air_quality_proxy(gas_resistance):
    # ideally, we would use the Bosch BSEC Library
    # however that is only compatible with arduinos and is closed source
    # this is a proxy
    return (gas_resistance-BME_GAS_MIN)/(BME_GAS_THRESHOLD-BME_GAS_MIN)

def get_lux_proxy(adc_value):
    voltage = ADC_REF * (float(adc_value)/float(ADC_HIGH))
    v = max(min(voltage, PHOTORESISTOR_MAX), PHOTORESISTOR_MIN)

    # Inverted so smaller = darker
    return (PHOTORESISTOR_MAX-v) / (PHOTORESISTOR_MAX - PHOTORESISTOR_MIN)

def get_gps_data(gps: adafruit_gps.GPS):
    if not gps.has_fix:
        return -3, -3
    return gps.latitude, gps.longitude

# Allow pico to communicate with GPS
tx_pin = board.GP0  # can be any pin marked TX (see pin map diagram)
rx_pin = board.GP1  # can be any pin marked RX (see pin map diagram)
uart = busio.UART(tx_pin, rx_pin, baudrate=9600, timeout=10)

# Temporarily turning debug to True so you can watch the fix happen!
gps = adafruit_gps.GPS(uart, debug = True) 

# Turn on the basic GGA and RMC info (REQUIRED for has_fix to work!)
gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
gps.send_command(b"PMTK220,1000")  # 1Hz update rate

# Data sending loop
last_transmit = time.monotonic()

try:
    while True:
        # Maintain GPS and MQTT to avoid any timeout
        gps.update()
        try:
            mqtt_client.loop()
        except Exception as e:
            print("MQTT Loop Error:", e)

        # Check that one time has passed to ensure we're only transmitting at 1 Hz
        current_time = time.monotonic()
        if current_time - last_transmit >= 1.0:
            last_transmit = current_time  # Reset the stopwatch

            latitude, longitude = get_gps_data(gps)

            # Convert python dictionary to json
            string = json.dumps({
                ID: MODULE_ID, 
                TEMPERATURE: bme.temperature, 
                HUMIDITY: bme.relative_humidity, 
                PRESSURE: bme.pressure, 
                GAS: get_air_quality_proxy(bme.gas), 
                LIGHT: get_lux_proxy(photoresistor.value), 
                LATITUDE: latitude,
                LONGITUDE: longitude
            })
            
            # Send json string to laptop
            mqtt_client.publish("station/" + str(MODULE_ID) + '/data', string)
            print("Sent:", string)

except KeyboardInterrupt:  # Clean exit instead of hard crash
    pass
