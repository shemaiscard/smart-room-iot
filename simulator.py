import paho.mqtt.client as mqtt
import time
import random

# MQTT Configuration (Giscard Unique Topics)
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC_TEMP = "giscard/smart_room/temp"
TOPIC_HUM = "giscard/smart_room/hum"

# Unique Client ID for your PC
client_id = f"giscard-sim-{random.randint(1000, 9999)}"
client = mqtt.Client(client_id=client_id)

print(f"Connecting to {BROKER} as {client_id}...")
try:
    client.connect(BROKER, PORT, 60)
    print("Connected successfully!")
    print(f"Publishing to: {TOPIC_TEMP} and {TOPIC_HUM}")
except Exception as e:
    print(f"Failed to connect: {e}")
    exit(1)

print("Starting simulation... Press Ctrl+C to stop.")
try:
    while True:
        temp = 22 + random.uniform(-2, 8)
        hum = 45 + random.uniform(-5, 15)
        
        client.publish(TOPIC_TEMP, f"{temp:.2f}")
        client.publish(TOPIC_HUM, f"{hum:.2f}")
        
        print(f"[{time.strftime('%H:%M:%S')}] Sent: Temp={temp:.2f}, Hum={hum:.2f}")
        time.sleep(5)
except KeyboardInterrupt:
    print("\nSimulation stopped.")
    client.disconnect()
