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
import computation

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

latest_wind_pairs = []

def get_current_data():
    """Return (modules, wind_pairs)."""
    global latest_wind_pairs

    if not USE_MQTT:
        parsed = [json.loads(s) for s in TEST_STRINGS]
        modules = [d for d in parsed if isinstance(d, dict) and ID in d]
        wind = []
        for d in parsed:
            if isinstance(d, dict) and WIND_PROXY in d:
                wind = d[WIND_PROXY] or []
                break
        latest_wind_pairs = wind
        return modules, wind

    output, pairs = computation.get_data()   # <-- tuple from computation
    modules = [json.loads(s) for s in output]
    latest_wind_pairs = pairs or []
    return modules, latest_wind_pairs

def get_current_modules():
    modules, _ = get_current_data()
    return modules

def get_current_wind_pairs():
    return latest_wind_pairs

# MQTT Functions

USE_MQTT = False #HIGHLIGHTING####################################################################################
TEST_STRINGS = sample
# TEST_STRINGS = [module1_data, module2_data, module3_data]

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

    rate_of_spread = 0
    
    if len(fire_positions) > 1:
        fire_plots = []
        for index in range(len(fire_positions)):
            fire_plots.append((((fire_positions[0][0] - fire_positions[index][0])*2) + ((fire_positions[0][1] - fire_positions[index][1])*2))*(0.5))

        rate_of_spread, _ = np.polyfit(fire_plots, times, 1)

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 6))
    scatter = ax.scatter(fires_x, fires_y, color="red", s=500, marker="o", alpha=0.3)
    scatter = ax.scatter(long, lat, c=temps, marker="s", alpha=0.6, cmap="coolwarm")
    ros_text = ax.text(min(long), max(lat), f"Rate of spread: {rate_of_spread} m/s")
    cbar = fig.colorbar(scatter, ax=ax, label="Temperature")

    # create initial arrows
    xs, ys, U_plot, V_plot = compute_weighted_wind_vectors(modlist)
    quiver = ax.quiver(
        xs, ys, U_plot, V_plot,
        angles="xy",
        scale_units="xy",
        scale=1,
        color="black",
        width=0.004,
        zorder=4
    )

    ax.set_xlabel("Longitude")
    # ax.set_xlim(min(long) + min(long)*0.05, max(long) - max(long)*0.05)
    ax.set_ylabel("Latitude")
    # ax.set_ylim(min(lat) + min(lat)*0.05, max(lat) - max(lat)*0.05)

    return fig, ax, scatter, cbar, quiver, ros_text

def identify_fire(mod):
    """Returns True if a module meets the threshold criteria to identify a fire"""
    if (mod[TEMPERATURE] >= 80) and (mod[LIGHT] >= 1):
        return True
    return False

def update_modules(_frame, ax, scatter, cbar, quiver_holder, ros_text):
    '''Continuously updates values (animation function for heatmap)'''
    start = time.perf_counter()

    modlist = get_current_modules()
    if not modlist:
        return scatter, quiver_holder["artist"]

    temps = np.array(get_values_list(modlist, TEMPERATURE), dtype=float)
    long = np.array(get_values_list(modlist, LONGITUDE), dtype=float)
    lat = np.array(get_values_list(modlist, LATITUDE), dtype=float)

    scatter.set_offsets(np.column_stack((long, lat)))
    scatter.set_array(temps)

    if temps.size > 0:
        scatter.set_clim(float(temps.min()), float(temps.max()))
        cbar.update_normal(scatter)
    
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

    rate_of_spread = 0
    
    if len(fire_positions) > 1:
        fire_plots = []
        for index in range(len(fire_positions)):
            fire_plots.append((((fire_positions[0][0] - fire_positions[index][0])*2) + ((fire_positions[0][1] - fire_positions[index][1])*2))*(0.5))

        rate_of_spread, _ = np.polyfit(fire_plots, times, 1)

    if len(fire_positions) > 1:
        fire_plots = []
        for index in range(len(fire_positions)):
            fire_plots.append((((fire_positions[0][0] - fire_positions[index][0])*2) + ((fire_positions[0][1] - fire_positions[index][1])*2))*(0.5))

        rate_of_spread, _ = np.polyfit(fire_plots, times, 1)
    
    if not hasattr(update_modules, "_fire_artist"):
        if len(ax.collections) > 0:
            update_modules._fire_artist = ax.collections[0] # type: ignore
        else:
            update_modules._fire_artist = ax.scatter(  # type: ignore
                [], [], color="red", s=500, marker="o", alpha=0.3, zorder=5
            )

    fire_offsets = (
        np.column_stack((fires_x, fires_y))
        if len(fires_x) > 0
        else np.empty((0, 2))
    )

    update_modules._fire_artist.set_offsets(fire_offsets)  # type: ignore


    xs, ys, U_plot, V_plot = compute_weighted_wind_vectors(modlist)

    q = quiver_holder["artist"]
    n_new = U_plot.size

    # Quiver cannot change arrow count via set_UVC; recreate if size changed
    if q.N != n_new:
        q.remove()
        q = ax.quiver(
            xs, ys, U_plot, V_plot,
            angles="xy",
            scale_units="xy",
            scale=1,
            color="black",
            width=0.004,
            zorder=4
        )
        quiver_holder["artist"] = q
    else:
        q.set_offsets(np.column_stack((xs, ys)))
        q.set_UVC(U_plot, V_plot)
    
    ros_text.set_position((float(np.min(long)), float(np.max(lat))))
    ros_text.set_text(f"Rate of spread: {rate_of_spread:.3f} m/s")

    return scatter, quiver_holder["artist"]

def get_data_for_module_id(modlist, id):
    '''Returns data of module i'''

    for mod in modlist:
        if mod[ID] == int(id):
            return f"Module {mod[ID]} \n Temperature: {mod[TEMPERATURE]} \n Pressure: {mod[PRESSURE]} \n Air Quality: {mod[GAS]} \n Light: {mod[LIGHT]} \n Coordinates: {(mod[LONGITUDE], mod[LATITUDE])}"
    return "Invalid ID"

def compute_weighted_wind_vectors(modlist):
    """
    For each node, compute one combined wind-direction proxy vector
    using all pairwise pressure differences.

    Returns:
        xs, ys, U_plot, V_plot
    """
    n = len(modlist)

    xs = np.array(get_values_list(modlist, LONGITUDE), dtype=float)
    ys = np.array(get_values_list(modlist, LATITUDE), dtype=float)
    ps = np.array(get_values_list(modlist, PRESSURE), dtype=float)
    U = np.zeros(n, dtype=float)
    V = np.zeros(n, dtype=float)

    for i in range(n):
        vx = 0.0
        vy = 0.0
        total_weight = 0.0

        for j in range(n):
            if i == j:
                continue

            dx = xs[j] - xs[i]
            dy = ys[j] - ys[i]
            dist = np.hypot(dx, dy)

            if dist < 1e-9:
                continue

            # unit vector from node i to node j
            ux = dx / dist
            uy = dy / dist

            # pressure difference
            delta_p = ps[i] - ps[j]

            # weight: bigger pressure difference + closer distance => stronger effect
            weight = abs(delta_p) / dist

            # if ps[i] > ps[j], contribution points from i toward j
            # if ps[i] < ps[j], contribution points opposite to (i->j)
            vx += weight * np.sign(delta_p) * ux
            vy += weight * np.sign(delta_p) * uy
            total_weight += weight

        if total_weight > 0:
            U[i] = vx / total_weight
            V[i] = vy / total_weight
        else:
            U[i] = 0.0
            V[i] = 0.0

    # normalize for display so arrows are visible and similar in length
    mags = np.hypot(U, V)
    U_plot = np.zeros_like(U)
    V_plot = np.zeros_like(V)

    nonzero = mags > 1e-9
    if np.any(nonzero):
        display_len = 0.05   # arrow display length on the graph
        U_plot[nonzero] = U[nonzero] / mags[nonzero] * display_len
        V_plot[nonzero] = V[nonzero] / mags[nonzero] * display_len


    return xs, ys, U_plot, V_plot

# User Interface
def interface():
    num = e.get()
    output = get_data_for_module_id(get_current_modules(), num)
    myLabel = tk.Label(root, text=output)
    myLabel.pack()

# RUN
if __name__ == "__main__":

    initial = []
    while not initial:
        initial = get_current_modules()

    fig, ax, scatter, cbar, quiver, ros_text = initialize_module_plot(initial)

    quiver_holder = {"artist": quiver}

    ani = FuncAnimation(
        fig,
        update_modules,
        interval=500,
        fargs=(ax, scatter, cbar, quiver_holder,ros_text),
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
