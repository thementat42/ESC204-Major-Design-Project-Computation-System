from matplotlib.axes import Axes
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
import tkinter as tk
import json
import threading
import paho.mqtt.client as mqtt
from data_keys import *

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
latest_records: dict[str, dict] = {}
records_lock = threading.Lock()


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
TEST_STRINGS = [module1_data, module2_data, module3_data]


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
        with records_lock:
            live = list(latest_records.values())
            if live:
                return live
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
    return [json.loads(module) for module in modules]

def get_values_list(modlist, metric):
    """Get a given metric from all modules"""
    return[module[metric] for module in modlist]

def initialize_module_plot(modlist):
    temps = np.array(get_values_list(modlist, TEMPERATURE), dtype=float)
    long = np.array(get_values_list(modlist, LONGITUDE), dtype=float)
    lat = np.array(get_values_list(modlist, LATITUDE), dtype=float)

    fig, ax = plt.subplots()
    scatter = ax.scatter(long, lat, c=temps, marker="s", alpha=0.6, cmap="coolwarm")
    cbar = fig.colorbar(scatter, ax=ax, label="Temperature")

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    return fig, ax, scatter, cbar

def update_modules(frame, scatter, cbar):
    '''Continuously updates values (animation function for heatmap)'''

    modlist = get_current_modules()

    temps = np.array(get_values_list(modlist, TEMPERATURE), dtype=float)
    long = np.array(get_values_list(modlist, LONGITUDE), dtype=float)
    lat = np.array(get_values_list(modlist, LATITUDE), dtype=float)

    scatter.set_offsets(np.column_stack((long, lat)))
    scatter.set_array(temps)

    if temps.size > 0:
        scatter.set_clim(float(temps.min()), float(temps.max()))
        cbar.update_normal(scatter)

    return (scatter,)

def get_data_for_module_id(modlist, id):
    '''Returns data of module i'''

    for mod in modlist:
        if mod[ID] == int(id):
            return f"Module {mod[ID]} \n Temperature: {mod[TEMPERATURE]} \n Humidity: {mod[HUMIDITY]} \n Pressure: {mod[PRESSURE]} \n Air Quality: {mod[GAS]} \n Light: {mod[LIGHT]} \n Coordinates: {(mod[LONGITUDE], mod[LATITUDE])}"
    return "Invalid ID"
        
# User Interface
def interface():
    num = e.get()
    output = get_data_for_module_id(get_current_modules(), num)
    myLabel = tk.Label(root, text=output)
    myLabel.pack()

# _anim = None


def fit_linear_pressure_plane(xs, ys, ps):
    a_matrix = np.column_stack([xs, ys, np.ones(len(xs))])
    coeffs, *_ = np.linalg.lstsq(a_matrix, ps, rcond=None)
    a, b, c = coeffs
    return a, b, c

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
            ax.text(x + 0.05, y + 0.05, str(sid), fontsize=10, zorder=4)
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

    # global _anim
    # _anim = FuncAnimation(fig, refresh, interval=1000, cache_frame_data=False)

    plt.tight_layout()
    plt.show(block=True)

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

    try:
        if USE_MQTT:
            plot_realtime_pressure_map()
    finally:
        if mqtt_client is not None:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
