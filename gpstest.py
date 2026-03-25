import board
import busio
import adafruit_gps

# Initialize UART
tx_pin = board.GP16  # Pico TX
rx_pin = board.GP17  # Pico RX
uart = busio.UART(tx_pin, rx_pin, baudrate=9600, timeout=10)

# DEBUG IS TRUE! This will print everything the GPS says.
gps = adafruit_gps.GPS(uart, debug=True)

print("Listening to the GPS...")

while True:
    # gps.update() will automatically print the raw NMEA sentences to the console
    gps.update()
