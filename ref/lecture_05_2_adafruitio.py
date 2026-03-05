# SPDX-FileCopyrightText: 2022 Liz Clark for Adafruit Industries
# SPDX-License-Identifier: MIT

import os
import time
import ssl
import wifi
import socketpool
import microcontroller
import board
import busio
import adafruit_requests
from adafruit_io.adafruit_io import IO_HTTP, AdafruitIO_RequestError

wifi.radio.connect(os.getenv('CIRCUITPY_WIFI_SSID'), os.getenv('CIRCUITPY_WIFI_PASSWORD'))

aio_username = os.getenv('aio_username')
aio_key = os.getenv('aio_key')

pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())
# Initialize an Adafruit IO HTTP API object
io = IO_HTTP(aio_username, aio_key, requests)
print("connected to io")

try:
# get feed
    picowTemp_feed = io.get_feed("iotworkshop")
    print("got feed: iotworkshop")
    
except AdafruitIO_RequestError:
# if no feed exists, create one
    picowTemp_feed = io.create_new_feed("iotworkshop")
    

#  pack feed names into an array for the loop
feed_name = picowTemp_feed["key"]
print("feeds created")

clock = 300

while True:
    try:
        #  when the clock runs out..
        if clock > 5:
            #  read sensor
            data = microcontroller.cpu.temperature
            #  send sensor data to respective feeds
           
            io.send_data(feed_name, data)
            print("sent %0.1f" % data)
            time.sleep(1)
            #  print sensor data to the REPL
            print("\nCPU Temperature: %0.1f C" % data)
            print()
            time.sleep(1)
            #  reset clock
            clock = 0
        else:
            clock += 1
    # pylint: disable=broad-except
    #  any errors, reset Pico W
    except Exception as e:
        print("Error:\n", str(e))
        print("Resetting microcontroller in 10 seconds")
        time.sleep(10)
        microcontroller.reset()
    #  delay
    time.sleep(1)
    print(clock)
