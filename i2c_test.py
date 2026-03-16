import board, busio, time

sda_pin = board.GP14
scl_pin = board.GP15

i2c = busio.I2C(sda_pin, scl_pin)

while not i2c.try_lock():
    pass

print("I2C addresses found:", [hex(device) for device in i2c.scan()])

i2c.unlock()