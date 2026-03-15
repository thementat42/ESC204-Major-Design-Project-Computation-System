import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import pandas as pd

# ___________________________________________________________________
# TEST JSONS

module1_data = """
{

"id": 1,

"temperature": 26,

"humidity": 53,

"pressure": 100,

"gas": 75,

"light": 0.1133,

"latitude": 31.44,

"longitude": -20.35
}

"""
module2_data = """
{

"id": 2,

"temperature": 30,

"humidity": 45,

"pressure": 80,

"gas": 90,

"light": 0.1100,

"latitude": 20.44,

"longitude": -30.35
}

"""

module3_data = """
{

"id": 3,

"temperature": 50,

"humidity": 15,

"pressure": 120,

"gas": 100,

"light": 0.5000,

"latitude": 51.44,

"longitude": -2.35
}

"""

# ___________________________________________________________________
# MAIN CODE

# Tasks:
    # Make marker display (updates in real time)
    # Make markers temperature dependent
    # Make pygame display to search up specific modules

# Define a module
class module:
    def __init__(self, id, temperature, humidity, pressure, gas, light, latitude, longitude):
        self.id = id
        self.temperature = temperature
        self.humidity = humidity
        self.pressure = pressure
        self.gas = gas
        self.light = light
        self.coords = (latitude, longitude)
        self.next = None # Allows modules to be iterated through via a linked list

# Define a system of modules        
class system:
    def __init__(self):
        self.start = None
    
    def size(self):
        '''Returns the number of modules in the system'''

        if self.start == None:
            return 0

        num = 0 # The number of modules
        cur = self.start
        while cur:
            while cur.next != None:
                num += 1
                cur = cur.next
        
        return num

    def values(self, id):
        '''Returns the values of a given module of the specified index'''

        if self.start == None:
            return "System Empty"
        
        # Check the size of the system to make sure id not out of range
        num = 0 # The number of modules
        cur = self.start
        while cur:
            while cur.next != None:
                num += 1
                cur = cur.next
        
        if id > num:
            return "Invalid Index"
        
        # Find the module at the specified index
        cur = self.start
        for i in range(id - 1):
            cur = cur.next

        return cur.coords, cur.temperature, cur.humidity, cur.pressure, cur.gas, cur.light
    
    def add_module(self, temperature, humidity, pressure, gas, light, latitude, longitude):

        # Check the size of the system to make sure id not out of range or already in the system
        num = 0 # The number of modules
        cur = self.start
        while cur:
            while cur.next != None:
                num += 1
                cur = cur.next
        
        # Create a new module to add to the system
        new_module = module((num + 1), temperature, humidity, pressure, gas, light, latitude, longitude)
        cur = self.start
        for i in range(num - 1):
            cur = cur.next
        cur.next = new_module

# ___________________________________________________________________
# RUN

if __name__ == '__main__':



# ___________________________________________________________________
# PRACTICE

# def init():
#     line.set_data([], [])
#     return line,

# # Temporary Position Proxy
# x = np.random.randn(4)
# y = np.random.randn(4)

# Temporary temperature proxy

# t = np.random.randn(4)

# Map
# plt.rcParams['axes.facecolor'] = 'black'
#'YlOrRd' for yellow to red
# fig, axes = plt.subplots()
# axes.scatter(x, y, c=t, marker='s', s=40, alpha=0.6, cmap = 'coolwarm')
# vmin_val = 0
# vmax_val = 1
# im = axes.imshow(t, vmin=vmin_val, vmax=vmax_val)
# axes.set_xlabel('Longitude')
# axes.set_ylabel('Latitude')
# fig.colorbar(im, ax=axes.ravel().tolist(), shrink=0.7, label='Your Label Here')
# plt.show()

# plt.figure(figsize = (10, 6))
# plt.scatter(x, y, c=t, marker='s', s=40, alpha=0.6, cmap = 'coolwarm')
# plt.colorbar(label='Local Temperature')
# plt.xlabel('Longitude')
# plt.ylabel("Latitude")
# plt.show()
# ___________________________________________________________________