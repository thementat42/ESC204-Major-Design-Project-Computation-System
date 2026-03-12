import paho.mqtt.client as mqtt
import json

LAPTOP_IP = "192.168.2.45" # Change this depending on network and device

# Connection function to subscribe to the module data and print progress
# Used by the MQTT library automatically on connection
def on_connect(client, userdata, flags, rc):
    print("Connected to Picos")
    client.subscribe("station/+/data")
    print("Listening for modules")

# Function to load the json string sent by the modules
def on_message(client, userdata, msg):
    data = json.loads(msg.payload)
    print(data)

# Create MQTT client and wire to functions
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Opens the connection and waits for messages indefinitely
client.connect(LAPTOP_IP, 1883)
client.loop_forever()