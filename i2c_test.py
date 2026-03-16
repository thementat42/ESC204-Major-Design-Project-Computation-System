import board, busio, time

sda_pin = board.GP0
scl_pin = board.GP1

i2c = busio.I2C(scl_pin, sda_pin)

while not i2c.try_lock():
    pass

print("I2C addresses found:", [hex(device) for device in i2c.scan()])

i2c.unlock()

