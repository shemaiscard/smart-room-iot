import paho.mqtt.client as mqtt
import time
import random
import json

# MQTT Configuration
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC_TEMP = "smart_room/sensors/temp"
TOPIC_HUM = "smart_room/sensors/hum"

# Using a unique Client ID for your PC
client_id = f"python-sim-{random.randint(1000, 9999)}"
client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)

print(f"Connecting to broker: {BROKER} as {client_id}")
client.connect(BROKER, PORT, 60)

print("Starting simulation... Press Ctrl+C to stop.")
try:
    while True:
        temp = 20 + random.uniform(0, 10)
        hum = 40 + random.uniform(0, 20)
        
        client.publish(TOPIC_TEMP, f"{temp:.2f}")
        client.publish(TOPIC_HUM, f"{hum:.2f}")
        
        print(f"Published: Temp={temp:.2f}, Hum={hum:.2f}")
        time.sleep(5)
except KeyboardInterrupt:
    print("Simulation stopped.")
    client.disconnect()
