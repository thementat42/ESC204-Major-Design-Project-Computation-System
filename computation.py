import paho.mqtt.client as mqtt
import json
import math

LAPTOP_IP = "192.168.2.45" # Change this depending on network and device

modules = {}

# Connection function to subscribe to the module data and print progress
# Used by the MQTT library automatically on connection
def on_connect(client, userdata, flags, rc):
    print("Connected to Picos")
    client.subscribe("station/+/data")
    print("Listening for modules")

# Function to load the json string sent by the modules
# Adds the data to a dictionary where each module key has a list of all readings
def on_message(client, userdata, msg):
    data = json.loads(msg.payload)
    module_id = data["id"]

    if module_id not in modules:
        modules[module_id] = []

    modules[module_id].append(data)
    print(f"[{module_id}] temp={data['temperature']}C pressure={data['pressure']}  gas={data['gas']}ohms")

    # Compute the wind proxy
    wind = compute_wind_proxy()
    if wind is not None:
        print(f"Wind proxy: {wind}")
        
# Function to calculate the wind speed proxy
def compute_wind_proxy():
    if len(modules) < 2:
        return None
    
    pressures = []
    for module_id in modules:
        latest = modules[module_id][-1]
        pressures.append(latest["pressure"])

    delta_p = max(pressures) - min(pressures)
    wind_proxy = math.sqrt(delta_p)

    return wind_proxy

# Create MQTT client and wire to functions
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Opens the connection and waits for messages indefinitely
client.connect(LAPTOP_IP, 1883)
client.loop_forever()

