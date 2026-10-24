import paho.mqtt.client as mqtt
import os
import time
import random

import secure_msg

# Stands in for the board: publishes signed readings so the dashboard's live
# mode can be tested without hardware. Needs the same SMART_ROOM_KEY as the
# dashboard, from the environment:
#   SMART_ROOM_KEY=... python simulator.py

# MQTT Configuration (Giscard Unique Topics)
BROKER = os.environ.get("MQTT_HOST", "broker.hivemq.com")
PORT = int(os.environ.get("MQTT_PORT", "8883"))
USE_TLS = os.environ.get("MQTT_USE_TLS", "1").lower() not in ("0", "false", "no")
TOPIC_BASE = os.environ.get("TOPIC_BASE", "giscard/smart_room")
TOPIC_TEMP = f"{TOPIC_BASE}/temp"
TOPIC_HUM = f"{TOPIC_BASE}/hum"
KEY = os.environ.get("SMART_ROOM_KEY", "").encode()
if not KEY:
    print("Set SMART_ROOM_KEY (the same key as the dashboard and the board).")
    exit(1)

# Unique Client ID for your PC
client_id = f"giscard-sim-{random.randint(1000, 9999)}"
client = mqtt.Client(client_id=client_id)
if USE_TLS:
    client.tls_set()
if os.environ.get("MQTT_USER"):
    client.username_pw_set(os.environ["MQTT_USER"], os.environ.get("MQTT_PASS", ""))

print(f"Connecting to {BROKER}:{PORT} as {client_id}...")
try:
    client.connect(BROKER, PORT, 60)
    client.loop_start()
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

        client.publish(TOPIC_TEMP, secure_msg.sign(KEY, TOPIC_TEMP, f"{temp:.2f}"))
        client.publish(TOPIC_HUM, secure_msg.sign(KEY, TOPIC_HUM, f"{hum:.2f}"))

        print(f"[{time.strftime('%H:%M:%S')}] Sent: Temp={temp:.2f}, Hum={hum:.2f}")
        time.sleep(1)
except KeyboardInterrupt:
    print("\nSimulation stopped.")
    client.loop_stop()
    client.disconnect()
