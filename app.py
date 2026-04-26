import streamlit as st
import paho.mqtt.client as mqtt
import pandas as pd
import plotly.graph_objects as go
import time
import random
from datetime import datetime
import queue

# Page Configuration
st.set_page_config(
    page_title="Smart Room IoT Dashboard",
    page_icon="🏠",
    layout="wide",
)

# Custom CSS for Premium Look
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric {
        background-color: #161b22;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #30363d;
    }
    </style>
    """, unsafe_allow_html=True)

# Global Data Bridge (Thread-safe)
if 'data_queue' not in st.session_state:
    st.session_state.data_queue = queue.Queue()

# Session State for History
if 'temp_history' not in st.session_state:
    st.session_state.temp_history = []
if 'hum_history' not in st.session_state:
    st.session_state.hum_history = []
if 'time_history' not in st.session_state:
    st.session_state.time_history = []
if 'light_status' not in st.session_state:
    st.session_state.light_status = "OFF"
if 'fan_status' not in st.session_state:
    st.session_state.fan_status = "OFF"
if 'door_locked' not in st.session_state:
    st.session_state.door_locked = True
if 'last_mqtt_update' not in st.session_state:
    st.session_state.last_mqtt_update = None

# MQTT Configuration
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
TOPIC_TEMP = "giscard/smart_room/temp"
TOPIC_HUM = "giscard/smart_room/hum"
TOPIC_CONTROL = "giscard/smart_room/control"

# Callback MUST NOT use st.session_state directly (it's in a different thread)
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe([(TOPIC_TEMP, 0), (TOPIC_HUM, 0)])

def on_message(client, userdata, msg):
    try:
        topic = msg.topic
        payload = float(msg.payload.decode())
        # Use a queue to send data back to the main thread
        userdata['queue'].put((topic, payload))
    except Exception as e:
        pass

# Sidebar
st.sidebar.title("⚙️ System Settings")
mode = st.sidebar.radio("Operation Mode", ["Simulated", "Live MQTT"], key="mode_selection")

# Reset on mode switch
if 'last_mode' not in st.session_state:
    st.session_state.last_mode = mode
if st.session_state.last_mode != mode:
    st.session_state.temp_history = []
    st.session_state.hum_history = []
    st.session_state.time_history = []
    st.session_state.last_mqtt_update = None
    st.session_state.last_mode = mode
    st.rerun()

# MQTT Client Setup
if 'mqtt_client' not in st.session_state and mode == "Live MQTT":
    client_id = f"giscard-dash-{random.randint(1000, 9999)}"
    # Pass the queue to the client via userdata
    client = mqtt.Client(client_id=client_id, userdata={'queue': st.session_state.data_queue})
    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        st.session_state.mqtt_client = client
        st.sidebar.success(f" Connected: {client_id}")
    except Exception as e:
        st.sidebar.error(f" Connection Error: {e}")

# Process Queue Data (Main Thread)
while not st.session_state.data_queue.empty():
    topic, val = st.session_state.data_queue.get()
    now = datetime.now().strftime("%H:%M:%S")
    st.session_state.last_mqtt_update = datetime.now()
    
    last_temp = st.session_state.temp_history[-1] if st.session_state.temp_history else 0.0
    last_hum = st.session_state.hum_history[-1] if st.session_state.hum_history else 0.0

    if topic == TOPIC_TEMP:
        st.session_state.temp_history.append(val)
        st.session_state.hum_history.append(last_hum)
    else:
        st.session_state.temp_history.append(last_temp)
        st.session_state.hum_history.append(val)
    
    st.session_state.time_history.append(now)
    
    if len(st.session_state.temp_history) > 30:
        st.session_state.temp_history.pop(0)
        st.session_state.hum_history.pop(0)
        st.session_state.time_history.pop(0)

# Main Dashboard UI
st.title(" Smart Room Control Center")

if mode == "Live MQTT":
    if st.session_state.last_mqtt_update:
        secs_ago = (datetime.now() - st.session_state.last_mqtt_update).total_seconds()
        if secs_ago < 10:
            st.success(f"● Receiving Live Data (Last update {int(secs_ago)}s ago)")
        else:
            st.warning(f"● Waiting for Data (Last update {int(secs_ago)}s ago)")
    else:
        st.info("● Waiting for first MQTT message... (Running simulator.py?)")

st.markdown("---")

# Metrics
col1, col2, col3 = st.columns(3)
if mode == "Simulated":
    t = 22 + random.uniform(-1, 1)
    h = 45 + random.uniform(-2, 2)
    now = datetime.now().strftime("%H:%M:%S")
    st.session_state.temp_history.append(t); st.session_state.hum_history.append(h); st.session_state.time_history.append(now)
    if len(st.session_state.temp_history) > 30:
        st.session_state.temp_history.pop(0); st.session_state.hum_history.pop(0); st.session_state.time_history.pop(0)
    curr_t, curr_h = t, h
else:
    curr_t = st.session_state.temp_history[-1] if st.session_state.temp_history else 0
    curr_h = st.session_state.hum_history[-1] if st.session_state.hum_history else 0

with col1: st.metric(" Temperature", f"{curr_t:.1f} °C")
with col2: st.metric(" Humidity", f"{curr_h:.1f} %")
with col3: st.metric(" Status", "System Online", delta="Live" if mode == "Live MQTT" else "Mock")

# Chart
fig = go.Figure()
if st.session_state.time_history:
    fig.add_trace(go.Scatter(x=st.session_state.time_history, y=st.session_state.temp_history, name="Temp (°C)", line=dict(color='#FF4B4B', width=2)))
    fig.add_trace(go.Scatter(x=st.session_state.time_history, y=st.session_state.hum_history, name="Hum (%)", line=dict(color='#0068C9', width=2)))
fig.update_layout(template="plotly_dark", height=400, margin=dict(l=20, r=20, t=20, b=20))
st.plotly_chart(fig, use_container_width=True)

# Control Panel
st.markdown("###  Remote Control Panel")
c1, c2, c3 = st.columns(3)

def send_cmd(device, state):
    if mode == "Live MQTT" and 'mqtt_client' in st.session_state:
        st.session_state.mqtt_client.publish(TOPIC_CONTROL, f"{device}:{state}")

with c1:
    if st.button("💡 Toggle Lights"):
        st.session_state.light_status = "OFF" if st.session_state.light_status == "ON" else "ON"
        send_cmd("LIGHT", st.session_state.light_status)
    st.info(f"Lights: {st.session_state.light_status}")

with c2:
    if st.button("🌀 Toggle Fan"):
        st.session_state.fan_status = "OFF" if st.session_state.fan_status == "ON" else "ON"
        send_cmd("FAN", st.session_state.fan_status)
    st.info(f"Fan: {st.session_state.fan_status}")

with c3:
    if st.button("🔒 Toggle Door"):
        st.session_state.door_locked = not st.session_state.door_locked
        send_cmd("DOOR", "LOCK" if st.session_state.door_locked else "UNLOCK")
    st.info(f"Door: {('LOCKED' if st.session_state.door_locked else 'UNLOCKED')}")

st.markdown("---")
st.caption(f"Refreshed: {datetime.now().strftime('%H:%M:%S')} | Topics: {TOPIC_TEMP}")
time.sleep(2)
st.rerun()
