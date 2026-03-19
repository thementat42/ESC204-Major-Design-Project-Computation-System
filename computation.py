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
    pairs = compute_wind_proxy()
    if pairs:
        for p in pairs:
            print(f"  {p['module_a']}-{p['module_b']}: delta={p['delta_p']:.2f}hPa magnitude={p['magnitude']:.2f}")

# Function to calculate the wind speed proxy
def compute_wind_proxy():
    if len(modules) < 2:
        return None
    
    pairs = []
    module_ids = list(modules.keys())

    # Nested loop to get every unique pair of modules
    for i in range(len(module_ids)):
        for j in range(i + 1, len(module_ids)):

            # Get the two module ids
            id_a = module_ids[i]
            id_b = module_ids[j]

            # Also get their latest pressure readings
            pres_a = modules[id_a][-1]["pressure"]
            pres_b = modules[id_b][-1]["pressure"]

            # Calculate direction info and magnitude
            delta_p = pres_a - pres_b
            magnitude = math.sqrt(abs(delta_p))

            pairs.append({"module_a": id_a, "module_b": id_b, "delta_p": delta_p, "magnitude": magnitude})

# Create MQTT client and wire to functions
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Opens the connection and waits for messages indefinitely
client.connect(LAPTOP_IP, 1883)
client.loop_forever()

