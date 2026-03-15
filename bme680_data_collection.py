import board
import analogio
import adafruit_bme680
import busio
import time

scl_pin = board.GP1  # can be any pin marked SCL
sda_pin = board.GP0  # can be any pin marked SDA

i2c = busio.I2C(scl_pin, sda_pin)
bme680_sensor = adafruit_bme680.Adafruit_BME680_I2C(i2c, address = 0x76)

gases = []
try:
    while True:
        gases.append(bme680_sensor.gas)
        print("Gas:", bme680_sensor.gas)
        time.sleep(2)
except KeyboardInterrupt:
    print(gases)
    exit()
