import paho.mqtt.client as mqtt
import time
import random
import json

# MQTT Configuration
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC_TEMP = "smart_room/sensors/temp"
TOPIC_HUM = "smart_room/sensors/hum"

client = mqtt.Client()

print(f"Connecting to broker: {BROKER}")
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
