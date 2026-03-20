from matplotlib.axes import Axes
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
import tkinter as tk
import json
import threading
import paho.mqtt.client as mqtt
from data_keys import *
import time
from computation import get_data

"""
Pressure / Gas Visualization (MQTT Version)

How this program works:
1. Sensor-side modules publish JSON messages over MQTT.
2. This visualization subscribes to MQTT topics:
       station/+/data
3. Each message is expected to look like:
       {"id": 1, "temperature": 23.1, "humidity": 40.2, "pressure": 1012.6, "gas": 123456}
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

# MQTT broker settings
BROKER_HOST = "127.0.0.1"
BROKER_PORT = 1883
MQTT_TOPIC = "station/+/data"

# Edit these positions if your physical sensor layout is different.
SENSOR_POSITIONS = {
    1: (0.0, 0.0),
    2: (2.0, 0.0),
    3: (2.0, 2.0),
    4: (0.0, 2.0),
}

# Shared sensor data storage
latest_records: dict[int, dict] = {}
records_lock = threading.Lock()

sample = ['{"ID": 1, "temperature": 80, "pressure": 1013.25, "gas": 0.78, "light": 1, "latitude": 43.6592, "longitude": -79.3972}','{"ID": 2, "temperature": 80, "pressure": 1012.85, "gas": 0.52, "light": 1, "latitude": 43.6610, "longitude": -79.3955}','{"ID": 3, "temperature": 21.10, "pressure": 1014.65, "gas": 0.91, "light": 0.43, "latitude": 43.6600, "longitude": -79.3980}','{"wind_proxy": [{"module_a": 1, "module_b": 2, "delta_p": 0.40, "magnitude": 0.63}, {"module_a": 1, "module_b": 3, "delta_p": -1.40, "magnitude": 1.18}, {"module_a": 2, "module_b": 3, "delta_p": -1.80, "magnitude": 1.34}]}']

module1_data = f"""
{{

"{ID}": 1,

"{TEMPERATURE}": 26,

"{HUMIDITY}": 53,

"{PRESSURE}": 100,

"{GAS}": 75,

"{LIGHT}": 0.1133,

"{LATITUDE}": 31.44,

"{LONGITUDE}": -20.35
}}

"""


module2_data = f"""
{{

"{ID}": 2,

"{TEMPERATURE}": 80,

"{HUMIDITY}": 53,

"{PRESSURE}": 100,

"{GAS}": 75,

"{LIGHT}": 0.1133,

"{LATITUDE}": 20.44,

"{LONGITUDE}": -30.35
}}

"""

module3_data = f"""
{{

"{ID}": 3,

"{TEMPERATURE}": 50,

"{HUMIDITY}": 15,

"{PRESSURE}": 120,

"{GAS}": 100,

"{LIGHT}": 0.5000,

"{LATITUDE}": 51.44,

"{LONGITUDE}": -2.35
}}

"""

# MQTT Functions

USE_MQTT = False
TEST_STRINGS = sample
# TEST_STRINGS = [module1_data, module2_data, module3_data]

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

def get_current_modules():
    if USE_MQTT:
        return get_data()
        # with records_lock:
        #     live = list(latest_records.values())
        #     if live:
        #         return live
    return create_module_list(TEST_STRINGS)


def start_mqtt_listener():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER_HOST, BROKER_PORT, 60)
    client.loop_start()
    return client

# Data vis helpers

def create_module_list(modules):
    """Create a list of modules (represented as dictionaries) from json strings"""
    return [json.loads(module) for module in modules[:-1]]

def get_wind_proxy_data(modules):
    """Get the data for the pressure gradients between modules, outputted as a list of json strings"""
    return [json.loads(module) for module in (modules[-1])]

def get_values_list(modlist, metric):
    """Get a given metric from all modules"""
    return[module[metric] for module in modlist]

def initialize_module_plot(modlist):

    start = time.time()

    # Set up heat map
    temps = np.array(get_values_list(modlist, TEMPERATURE), dtype=float)
    long = np.array(get_values_list(modlist, LONGITUDE), dtype=float)
    lat = np.array(get_values_list(modlist, LATITUDE), dtype=float)

    # Mark fires
    fires_x = []
    fires_y = []
    for mod in modlist:
        if identify_fire(mod):
            fires_x.append(mod[LONGITUDE])
            fires_y.append(mod[LATITUDE])

    # Compute rate of spread
    fire_positions = []
    times = []
    for mod in modlist:
        if identify_fire(mod) and ((mod[LONGITUDE], mod[LATITUDE]) not in fire_positions):
                fire_positions.append((mod[LONGITUDE], mod[LATITUDE]))
                end = time.time()
                timing = end - start
                times.append(timing)
    
    if len(fire_positions) > 1:
        fire_plots = []
        for index in range(len(fire_positions)):
            fire_plots.append((((fire_positions[0][0] - fire_positions[index][0])*2) + ((fire_positions[0][1] - fire_positions[index][1])*2))*(0.5))

        rate_of_spread, interface = np.polyfit(fire_plots, times, 1)

    # Create plot
    fig, ax = plt.subplots()
    scatter = ax.scatter(fires_x, fires_y, color="red", s=500, marker="o", alpha=0.3)
    scatter = ax.scatter(long, lat, c=temps, marker="s", alpha=0.6, cmap="coolwarm")
    ax.text(min(long), max(lat), f"Rate of spread: {rate_of_spread} m/s")
    cbar = fig.colorbar(scatter, ax=ax, label="Temperature")

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    return fig, ax, scatter, cbar

def get_data_for_module_id(modlist, id):
    '''Returns data of module i'''

    for mod in modlist:
        if mod[ID] == int(id):
            return f"Module {mod[ID]} \n Temperature: {mod[TEMPERATURE]} \n  Pressure: {mod[PRESSURE]} \n Air Quality: {mod[GAS]} \n Light: {mod[LIGHT]} \n Coordinates: {(mod[LONGITUDE], mod[LATITUDE])}"
    return "Invalid ID"

def identify_fire(mod):
    """Returns True if a module meets the threshold criteria to identify a fire"""
    if (mod[TEMPERATURE] >= 80) and (mod[LIGHT] >= 1):
        return True
    return False


def update_modules(scatter, cbar):
    '''Continuously updates values (animation function for heatmap)'''

    # Get module list
    modlist = get_current_modules()

    # Set up heat map
    temps = np.array(get_values_list(modlist, TEMPERATURE), dtype=float)
    long = np.array(get_values_list(modlist, LONGITUDE), dtype=float)
    lat = np.array(get_values_list(modlist, LATITUDE), dtype=float)

    scatter.set_offsets(np.column_stack((long, lat)))
    scatter.set_array(temps)

    if temps.size > 0:
        scatter.set_clim(float(temps.min()), float(temps.max()))
        cbar.update_normal(scatter)

    return (scatter,)
        
# User Interface
def interface():
    num = e.get()
    output = get_data_for_module_id(get_current_modules(), num)
    myLabel = tk.Label(root, text=output)
    myLabel.pack()

# RUN

if __name__ == "__main__":
    mqtt_client = start_mqtt_listener() if USE_MQTT else None

    initial = get_current_modules()
    fig, ax, scatter, cbar = initialize_module_plot(initial)
    ani = FuncAnimation(
        fig,
        update_modules,
        interval=500,
        fargs=(scatter, cbar),
        cache_frame_data=False
    )

    plt.tight_layout()
    plt.show(block=False)

    root = tk.Tk()
    e = tk.Entry(root, width=50)
    e.pack()

    myButton = tk.Button(root, text="Enter ID", command=interface)
    myButton.pack()

    root.mainloop()
