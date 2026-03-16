# <<<<<<< HEAD
import matplotlib.pyplot as plt
# import matplotlib.animation as animation
from matplotlib.animation import FuncAnimation
import numpy as np
import pandas as pd
import pygame as pg
from tkinter import *
# =======
"""
Pressure / Gas Visualization (MQTT Version)

How this program works:
1. Sensor-side modules publish JSON messages over MQTT.
2. This visualization subscribes to MQTT topics:
       station/+/data
3. Each message is expected to look like:
       {"id": "m01", "temperature": 23.1, "humidity": 40.2, "pressure": 1012.6, "gas": 123456}
4. The latest record from each sensor is stored and displayed.
5. Node color represents pressure.
6. The center/background is estimated from a linear pressure field fit.
7. Hover over a node to see pressure, temperature, humidity, and gas.
8. The plot refreshes automatically every second.

Requirements:
    pip install matplotlib numpy paho-mqtt

Run:
    python datavis.py

If your broker is not running on this computer, change BROKER_HOST below.
"""
# >>>>>>> ed27eac8edc5cbe9909b8b308b4b437690ed6e6b
import json
import threading
from typing import Dict
import paho.mqtt.client as mqtt

# MQTT broker settings
BROKER_HOST = "127.0.0.1"
BROKER_PORT = 1883
MQTT_TOPIC = "station/+/data"

# Edit these positions if your physical sensor layout is different.
SENSOR_POSITIONS = {
    "m01": (0.0, 0.0),
    "m02": (2.0, 0.0),
    "m03": (2.0, 2.0),
    "m04": (0.0, 2.0),
}

# Shared sensor data storage
latest_records: Dict[str, dict] = {}
records_lock = threading.Lock()

# <<<<<<< HEAD

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

"temperature": 80,

"humidity": 53,

"pressure": 100,

"gas": 75,

"light": 0.1133,

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
# Tasks:
    # Make module and system classes - DONE
    # Make marker display (updates in real time)
    # Make markers temperature dependent
    # Make pygame display to search up specific modules
    # Make a display function to runt the whole thing

# ___________________________________________________________________
# DICTIONARY REPRESENTATION

def module_list(modules):
    '''Creates a list of modules in the form of dictionaries'''

    mod_list = []
    for mod in modules:
        set = json.loads(mod)
        mod_list.append(set)
    return mod_list

def values_list(modlist, key):
    '''Extracts a given value type from each module in a list and outputs a list of those values (e.g. list of temperatures)'''
    values = [] #list of temperatures to plot

    for mod in modlist:
        values.append(mod[key])
    
    return values

def update(modlist):
    '''Continuously updates values (animation function for heatmap)'''
    t = "temperature"
    x = "longitude"
    y = "latitude"
    temps = values_list(modlist, t)
    # temps = [np.random.randn(2)]
    long = values_list(modlist, x)
    lat = values_list(modlist, y)
    
    plt.cla()

    plt.scatter(long, lat, c=temps, marker='s', alpha=0.6, cmap='coolwarm')
    plt.colorbar(label="Temperature")
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')

def id(modlist, i):
    '''Returns data of module i'''

    for mod in modlist:
        if mod["id"] == int(i):
            return f"Module {mod["id"]} \n Temperature: {mod["temperature"]} \n Humidity: {mod["humidity"]} \n Pressure: {mod["pressure"]} \n Air Quality: {mod["gas"]} \n Light: {mod["light"]} \n Coordinates: {(mod["longitude"], mod["latitude"])}"
    return "Invalid ID"
        
# User Interface
def Interface(modlist):
    num = e.get()
    output = id(modlist, num)
    myLabel = Label(root, text=output)
    myLabel.pack()

# ___________________________________________________________________
# LINKED LIST REPRESENTATION
# Define a module
# class module:
#     def __init__(self, id, temperature, humidity, pressure, gas, light, latitude, longitude):
#         self.id = id
#         self.temperature = temperature
#         self.humidity = humidity
#         self.pressure = pressure
#         self.gas = gas
#         self.light = light
#         self.coords = (latitude, longitude)
#         self.next = None # Allows modules to be iterated through via a linked list

# # Define a system of modules        
# class system:
#     def __init__(self):
#         self.start = None
    
#     def size(self):
#         '''Returns the number of modules in the system'''

#         if self.start == None:
#             return 0

#         num = 0 # The number of modules
#         cur = self.start
#         while cur:
#             while cur.next != None:
#                 num += 1
#                 cur = cur.next
        
#         return num

#     def values(self, id):
#         '''Returns the values of a given module of the specified index'''

#         if self.start == None:
#             return "System Empty"
        
#         # Check the size of the system to make sure id not out of range
#         num = 0 # The number of modules
#         cur = self.start
#         while cur:
#             while cur.next != None:
#                 num += 1
#                 cur = cur.next
        
#         if id > num:
#             return "Invalid Index"
        
#         # Find the module at the specified index
#         cur = self.start
#         for i in range(id - 1):
#             cur = cur.next

#         return cur.coords, cur.temperature, cur.humidity, cur.pressure, cur.gas, cur.light
    
#     def add_module(self, new_module):
#         '''Adds a new module'''

#         # Check the size of the system 
#         num = 0 # The number of modules
#         cur = self.start
#         while cur:
#             while cur.next != None:
#                 num += 1
#                 cur = cur.next
        
#         # new_module = module((num + 1), temperature, humidity, pressure, gas, light, latitude, longitude)
#         if self.start == None:
#             self.start = new_module
        
#         # Create a new module to add to the system
#         cur = self.start
#         for i in range(num - 1):
#             cur = cur.next
#         cur.next = new_module
    
#     def update_module(self, id, temperature, humidity, pressure, gas, light):
#         '''Updates module values for display'''

#         if id == 1:
#             self.start.temperature = temperature
#             self.start.humidity = humidity
#             self.start.pressure = pressure
#             self.start.gas = gas
#             self.start.light = light

#         else:
#             cur = self.start
#             for i in range(id):
#                 cur = cur.next
#             cur.temperature = temperature
#             cur.humidity = humidity
#             cur.pressure = pressure
#             cur.gas = gas
#             cur.light = light

# def extract_values(string):
#     '''Exctract data from a json string and create a module out of it'''
#     set = json.loads(string)

#     id = set["id"]
#     temperature = set["temperature"]
#     humidity = set["humidity"]
#     pressure = set["pressure"]
#     gas = set["gas"]
#     light = set["light"]
#     latitude = set["latitude"]
#     longitude = set["longitude"]

#     mod = module(id, temperature, humidity, pressure, gas, light, latitude, longitude)

#     return mod

# def create_system(list):
#     '''Takes in a list of json strings and makes a linked list (system) of modules out of them'''
#     sys = system()
#     for string in list:
#         new_mod = extract_values(string)
#         sys.add_module(new_mod)
#     return sys

# ___________________________________________________________________
# PRESSURE MAPPING
# =======
_anim = None
# >>>>>>> ed27eac8edc5cbe9909b8b308b4b437690ed6e6b


def fit_linear_pressure_plane(xs, ys, ps):
    a_matrix = np.column_stack([xs, ys, np.ones(len(xs))])
    coeffs, _, _, _ = np.linalg.lstsq(a_matrix, ps, rcond=None)
    a, b, c = coeffs
    return a, b, c


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker.")
        client.subscribe(MQTT_TOPIC)
        print(f"Subscribed to topic: {MQTT_TOPIC}")
    else:
        print(f"Failed to connect to MQTT broker. Return code: {rc}")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        sensor_id = payload.get("id")
        if sensor_id:
            with records_lock:
                latest_records[sensor_id] = payload
    except Exception as e:
        print("Failed to parse MQTT message:", e)


def start_mqtt_listener():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER_HOST, BROKER_PORT, 60)
    client.loop_start()
    return client


def plot_realtime_pressure_map():
    fig, ax = plt.subplots(figsize=(7, 6))

    state = {
        "scatter": None,
        "annot": None,
        "sensor_ids": [],
        "records": {},
        "positions": {},
        "fixed_xlim": None,
        "fixed_ylim": None,
    }

    def make_annotation():
        annot = ax.annotate(
            "",
            xy=(0, 0),
            xytext=(16, 16),
            textcoords="offset points",
            bbox=dict(
                boxstyle="round,pad=0.6",
                fc="white",
                ec="0.4",
                alpha=0.98,
            ),
            fontsize=10,
        )
        annot.set_visible(False)
        return annot

    def draw_waiting_screen(message="Waiting for MQTT sensor data..."):
        ax.clear()
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])

        for spine in ax.spines.values():
            spine.set_visible(False)

        ax.text(
            0.5,
            0.5,
            message,
            ha="center",
            va="center",
            fontsize=12,
            transform=ax.transAxes,
            color="0.35",
        )

        state["scatter"] = None
        state["annot"] = None
        state["sensor_ids"] = []
        state["records"] = {}
        state["positions"] = {}
        state["fixed_xlim"] = None
        state["fixed_ylim"] = None

    def draw_frame(records):
        sensor_ids = [sid for sid in SENSOR_POSITIONS if sid in records]

        if not sensor_ids:
            draw_waiting_screen("No valid sensor records received yet.")
            return

        positions = {sid: SENSOR_POSITIONS[sid] for sid in sensor_ids}
        pressures = np.array([records[sid]["pressure"] for sid in sensor_ids], dtype=float)

        node_xs = np.array([positions[sid][0] for sid in sensor_ids], dtype=float)
        node_ys = np.array([positions[sid][1] for sid in sensor_ids], dtype=float)

        ax.clear()

        if state["fixed_xlim"] is None or state["fixed_ylim"] is None:
            fixed_margin = 0.8
            state["fixed_xlim"] = (
                float(node_xs.min()) - fixed_margin,
                float(node_xs.max()) + fixed_margin,
            )
            state["fixed_ylim"] = (
                float(node_ys.min()) - fixed_margin,
                float(node_ys.max()) + fixed_margin,
            )

        x_min, x_max = state["fixed_xlim"]
        y_min, y_max = state["fixed_ylim"]

        if len(sensor_ids) >= 3:
            a, b, c = fit_linear_pressure_plane(node_xs, node_ys, pressures)
            grid_x = np.linspace(x_min, x_max, 120)
            grid_y = np.linspace(y_min, y_max, 120)
            xx, yy = np.meshgrid(grid_x, grid_y)
            zz = a * xx + b * yy + c

            ax.contourf(xx, yy, zz, levels=20, cmap="coolwarm", alpha=0.35)
            ax.contour(xx, yy, zz, levels=8, colors="gray", linewidths=0.7, alpha=0.5)

        scatter = ax.scatter(
            node_xs,
            node_ys,
            s=180,
            c=pressures,
            cmap="coolwarm",
            edgecolors="black",
            linewidths=1.0,
            zorder=3,
        )

        for sid in sensor_ids:
            x, y = positions[sid]
            ax.text(x + 0.05, y + 0.05, sid, fontsize=10, zorder=4)
            ax.text(
                x + 0.05,
                y - 0.12,
                f"{records[sid]['pressure']:.2f} hPa",
                fontsize=8,
                color="0.25",
                zorder=4,
            )

        ax.set_title("Pressure Map (Linear Interpolation Assumption)", fontsize=12)
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])

        for spine in ax.spines.values():
            spine.set_visible(False)

        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)

        annot = make_annotation()

        state["scatter"] = scatter
        state["annot"] = annot
        state["sensor_ids"] = sensor_ids
        state["records"] = records
        state["positions"] = positions

    def update_annotation(ind):
        index = ind["ind"][0]
        sensor_id = state["sensor_ids"][index]
        record = state["records"][sensor_id]
        x, y = state["positions"][sensor_id]

        annot = state["annot"]
        annot.xy = (x, y)
        annot.set_text(
            f"{sensor_id}\n"
            f"Pressure: {record['pressure']:.2f} hPa\n"
            f"Temperature: {record['temperature']:.2f} °C\n"
            f"Humidity: {record['humidity']:.2f} %\n"
            f"Gas: {record['gas']}"
        )

    def on_hover(event):
        scatter = state["scatter"]
        annot = state["annot"]

        if scatter is None or annot is None:
            return

        if event.inaxes == ax:
            contains, ind = scatter.contains(event)
            if contains:
                update_annotation(ind)
                annot.set_visible(True)
                fig.canvas.draw_idle()
            else:
                if annot.get_visible():
                    annot.set_visible(False)
                    fig.canvas.draw_idle()

    def refresh(_):
        try:
            with records_lock:
                records_copy = dict(latest_records)

            if not records_copy:
                draw_waiting_screen("Waiting for MQTT sensor data...")
                return

            draw_frame(records_copy)

        except Exception as e:
            draw_waiting_screen(f"Update failed:\n{e}")

    fig.canvas.mpl_connect("motion_notify_event", on_hover)

    refresh(0)

    global _anim
    _anim = FuncAnimation(fig, refresh, interval=1000, cache_frame_data=False)

    plt.tight_layout()
    plt.show(block=True)

# ___________________________________________________________________
# RUN

if __name__ == "__main__":
    
    modules = [module1_data, module2_data, module3_data]
    sys = module_list(modules)
    ani = FuncAnimation(plt.gcf(), update(sys), interval = 500)
    plt.tight_layout()
    plt.show(block=False)

    print(id(sys, 2))

    root = Tk()

    e = Entry(root, width=50)
    e.pack()

    myButton = Button(root, text="Enter ID", command=lambda: Interface(sys))
    myButton.pack()

    root.mainloop()

    mqtt_client = start_mqtt_listener()
    try:
        plot_realtime_pressure_map()
    finally:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
    