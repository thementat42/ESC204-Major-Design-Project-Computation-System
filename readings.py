import board
import analogio
import adafruit_bme680
import adafruit_gps
import busio

DEBUG = False

# bme680 info:
# https://cdn-learn.adafruit.com/downloads/pdf/adafruit-bme680-humidity-temperature-barometic-pressure-voc-gas.pdf

# GPS info:
# https://learn.adafruit.com/adafruit-ultimate-gps/circuitpython-python-uart-usage

#BME680 outputs data as follows:
# Temperature in degrees celcius
# Resistance of gas sensor in Ohms
    # This is proportional to the amount of volatile organic compound particles (VOC) in the air
# Humidity as a percentage
# Pressure in hPa (hectoPascals = 100 Pascals)
# Altitude in metres (not used)

# set up the pins for the sensors
photoresistor = analogio.AnalogIn(board.GP26_A0)

i2c = board.I2C()
bme680_sensor = adafruit_bme680.Adafruit_BME680_I2C(i2c)

tx_pin = board.GP0  # can be any pin marked TX (see pin map diagram)
rx_pin = board.GP1  # can be any pin marked RX (see pin map diagram)
uart = busio.UART(tx_pin, rx_pin, baudrate=9600, timeout=10)

gps = adafruit_gps.GPS(uart, debug = DEBUG)


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
