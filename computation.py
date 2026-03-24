import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
import ssl
import json
import math
from _mqtt import *
import time

from data_keys import *

modules = {}

# Connection function to subscribe to the module data and print progress
# Used by the MQTT library automatically on connection
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Connected to Picos")
        client.subscribe("station/+/data")
        print("Listening for modules")
    else:
        print(f"Error {reason_code}")
        
        
# Function to load the json string sent by the modules
# Adds the data to a dictionary where each module key has a list of all readings
def on_message(client, userdata, msg):
    data = json.loads(msg.payload)
    module_id = data[ID]

    if module_id not in modules:
        modules[module_id] = []

    modules[module_id].append(data)
    print(f"[{module_id}] temp={data[TEMPERATURE]}C pressure={data[PRESSURE]}  gas={data[GAS]}%")

    # Compute the wind proxy
    pairs = compute_wind_proxy()
    if pairs:
        for p in pairs:
            print(f"  {p[MODULE_A]}-{p[MODULE_B]}: delta={p[DELTA_P]:.2f}hPa magnitude={p[MAGNITUDE]:.2f}")

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
            pres_a = modules[id_a][-1][PRESSURE]
            pres_b = modules[id_b][-1][PRESSURE]

            # Calculate direction info and magnitude
            delta_p = pres_a - pres_b
            magnitude = math.sqrt(abs(delta_p))

            pairs.append({MODULE_A: id_a, MODULE_B: id_b, DELTA_P: delta_p, MAGNITUDE: magnitude})

    return pairs

def get_data():
    output = []

    # Output builder loop
    for module_id in modules:
        # Make sure its not empty
        if len(modules[module_id]) > 0:
            # Get most recent reading
            latest = modules[module_id][-1]
            # Build the dictionary with what datavis needs
            filtered = {
                ID: latest[ID],
                TEMPERATURE: latest[TEMPERATURE],
                PRESSURE: latest[PRESSURE],
                GAS: latest[GAS],
                LIGHT: latest[LIGHT],
                LATITUDE: latest[LATITUDE],
                LONGITUDE: latest[LONGITUDE]

            }
            # Convert dict to json string
            output.append(json.dumps(filtered))

    # Run wind proxy calculation
    pairs = compute_wind_proxy()

    # Append wind proxy calculations
    if pairs:
        output.append(json.dumps({WIND_PROXY: pairs}))

    return output

# Create MQTT client and wire to functions
client = mqtt.Client(CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

client.tls_set(tls_version=ssl.PROTOCOL_TLS_CLIENT)
client.username_pw_set(HIVEMQ_USERNAME, HIVEMQ_PASSWORD)

# Opens the connection and waits for messages indefinitely
client.connect(HIVEMQ_HOST, 8883)
client.loop_start()

if __name__ == "__main__":    
    while True:
        output = get_data()
        print(output)
        time.sleep(1)

